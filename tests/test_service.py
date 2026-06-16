import pytest
from app.dataproc import RemoteMismatch
from app.validation import ApiError
from conftest import CALLER, OTHER, create, message, remote


def test_duplicate_deliveries_submit_once(env, payload):
    job = create(env, payload)
    env.service.process(message(job))
    env.service.process(message(job))
    env.dp.submit.assert_called_once()
    assert env.store.get(job['tenant'], job['job_id'])['remote_uuid'] == 'remote-unique-id'


def test_timeout_retries_with_original_native_ids(env, payload):
    job = create(env, payload)
    env.dp.submit.side_effect = TimeoutError('secret')
    env.service.process(message(job))
    assert env.store.get(job['tenant'], job['job_id'])['status'] == 'SUBMISSION_UNKNOWN'
    env.dp.get.side_effect = lambda _: None
    env.clock[0] += 121
    env.service.reconcile_one(job['tenant'], job['job_id'])
    env.dp.submit.side_effect = remote
    env.service.process(message(job))
    first, second = [call.args[0] for call in env.dp.submit.call_args_list]
    assert first['submission_id'] == second['submission_id'] == job['submission_id']
    assert first['dataproc_job_id'] == second['dataproc_job_id']
    assert second['attempts'] == 2


def test_lost_submit_response_attaches_existing_remote(env, payload):
    job = create(env, payload)
    env.dp.submit.side_effect = TimeoutError()
    env.service.process(message(job))
    env.clock[0] += 121
    env.service.reconcile_one(job['tenant'], job['job_id'])
    current = env.store.get(job['tenant'], job['job_id'])
    assert current['remote_uuid'] == 'remote-unique-id' and current['status'] == 'RUNNING'
    env.dp.submit.assert_called_once()


def test_crash_before_submit_can_recover(env, payload):
    job = create(env, payload)
    env.store.replace(job, status='SUBMITTING', attempts=1, submitted_at=env.clock[0])
    env.dp.get.side_effect = lambda _: None
    env.clock[0] += 121
    env.service.reconcile_one(job['tenant'], job['job_id'])
    env.service.process(message(job))
    env.dp.submit.assert_called_once()


def test_cancel_before_dispatch_prevents_execution(env, payload):
    job = create(env, payload)
    assert env.service.cancel(CALLER, job['job_id'])['status'] == 'CANCELLED'
    env.service.process(message(job))
    env.dp.submit.assert_not_called()


def test_cancel_racing_submission_is_preserved(env, payload):
    job = create(env, payload)
    def submit(value):
        env.service.cancel(CALLER, job['job_id'])
        return remote(value)
    env.dp.submit.side_effect = submit
    env.service.process(message(job))
    current = env.store.get(job['tenant'], job['job_id'])
    assert current['status'] == 'CANCEL_REQUESTED' and current['remote_uuid']
    env.clock[0] += 121
    env.service.reconcile_one(job['tenant'], job['job_id'])
    env.dp.cancel.assert_called_once()


def test_cancel_retry_queue_does_not_falsely_claim_cancelled(env, payload):
    job = create(env, payload)
    env.store.replace(job, attempts=1)
    assert env.service.cancel(CALLER, job['job_id'])['status'] == 'CANCEL_REQUESTED'
    env.dp.get.side_effect = lambda _: None
    env.clock[0] += 121
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['status'] == 'CANCEL_REQUESTED'
    env.dp.submit.assert_not_called()


def test_cancel_ack_does_not_override_remote_success(env, payload):
    job = create(env, payload)
    env.service.process(message(job))
    env.service.cancel(CALLER, job['job_id'])
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['cancel_accepted']
    env.clock[0] += 121
    env.dp.get.side_effect = lambda j: remote(j, 'DONE')
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['status'] == 'SUCCEEDED'


@pytest.mark.parametrize('attempts,age', [(5, 121), (1, 86401)])
def test_ambiguous_submission_has_bounded_retry_budget(env, payload, attempts, age):
    job = create(env, payload)
    env.store.replace(job, attempts=attempts, status='SUBMISSION_UNKNOWN', submitted_at=env.clock[0])
    env.dp.get.side_effect = lambda _: None
    env.clock[0] += age
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['status'] == 'NEEDS_REVIEW'
    env.dp.submit.assert_not_called()


def test_confirmed_remote_disappears_never_resubmitted(env, payload):
    job = create(env, payload)
    env.service.process(message(job))
    env.dp.get.side_effect = lambda _: None
    env.clock[0] += 121
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['reason'] == 'REMOTE_JOB_MISSING'
    env.dp.submit.assert_called_once()


def test_foreign_remote_is_not_cancelled(env, payload):
    job = create(env, payload)
    env.service.process(message(job))
    env.service.cancel(CALLER, job['job_id'])
    env.dp.get.side_effect = RemoteMismatch()
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['reason'] == 'REMOTE_IDENTITY_MISMATCH'
    env.dp.cancel.assert_not_called()

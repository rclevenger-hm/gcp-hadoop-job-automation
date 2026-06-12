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

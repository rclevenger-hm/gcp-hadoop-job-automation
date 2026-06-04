import pytest
from google.api_core.exceptions import AlreadyExists, NotFound, RequestRangeNotSatisfiable
from google.cloud import dataproc_v1
from app.dataproc import RemoteMismatch
from app.validation import ApiError
from conftest import create, remote


def test_submit_native_proto_and_stable_request_id(env, payload):
    job = create(env, payload)
    env.client.submit_job.return_value = remote(job)
    env.native.submit(job)
    kwargs = env.client.submit_job.call_args.kwargs
    proto = dataproc_v1.SubmitJobRequest(**kwargs['request'])
    assert proto.request_id == job['submission_id'] and len(proto.request_id) == 36
    assert proto.job.hadoop_job.main_class == payload['job_class']
    assert proto.job.hadoop_job.main_jar_file_uri == ''
    assert list(proto.job.hadoop_job.args) == [payload['input_path'], payload['output_path']]
    assert kwargs['retry'] is None and kwargs['timeout'] == 10
    assert not proto.job.scheduling.max_failures_total


def test_already_exists_resolves_exact_remote(env, payload):
    job = create(env, payload)
    env.client.submit_job.side_effect = AlreadyExists('existing')
    env.client.get_job.return_value = remote(job)
    assert env.native.submit(job).job_uuid == 'remote-unique-id'
    assert env.client.get_job.call_args.kwargs['request']['job_id'] == job['dataproc_job_id']


@pytest.mark.parametrize('field', ['project', 'job_id', 'cluster', 'label', 'class', 'jar', 'args', 'uuid'])
def test_remote_identity_fingerprint_fence(env, payload, field):
    job = create(env, payload)
    value = remote(job)
    if field == 'project':
        value.reference.project_id = 'other'
    elif field == 'job_id':
        value.reference.job_id = 'other'
    elif field == 'cluster':
        value.placement.cluster_name = 'other'
    elif field == 'label':
        value.labels['submission'] = 'other'
    elif field == 'class':
        value.hadoop_job.main_class = 'other'
    elif field == 'jar':
        value.hadoop_job.jar_file_uris = ['gs://evil/job.jar']
    elif field == 'args':
        value.hadoop_job.args = ['other']
    elif field == 'uuid':
        job['remote_uuid'] = 'previous-uuid'
    with pytest.raises(RemoteMismatch):
        env.native.verify(job, value)


def test_missing_remote_returns_none(env, payload):
    env.client.get_job.side_effect = NotFound('gone')
    assert env.native.get(create(env, payload)) is None


def test_cancel_checks_identity_before_mutation(env, payload):
    job = create(env, payload)
    env.client.get_job.return_value = remote(job)
    env.client.cancel_job.return_value = remote(job, 'CANCEL_PENDING')
    assert env.native.cancel(job)
    env.client.get_job.return_value = remote(job, uuid='replacement')
    job['remote_uuid'] = 'original'
    with pytest.raises(RemoteMismatch):
        env.native.cancel(job)
    env.client.cancel_job.assert_called_once()


@pytest.mark.parametrize('native,expected', [('PENDING', 'SUBMITTED'), ('SETUP_DONE', 'SUBMITTED'), ('RUNNING', 'RUNNING'), ('ATTEMPT_FAILURE', 'RUNNING'), ('CANCEL_PENDING', 'CANCEL_REQUESTED'), ('CANCEL_STARTED', 'CANCEL_REQUESTED'), ('DONE', 'SUCCEEDED'), ('ERROR', 'FAILED'), ('CANCELLED', 'CANCELLED')])
def test_native_state_map(env, payload, native, expected):
    assert env.native.state(remote(create(env, payload), native)) == expected

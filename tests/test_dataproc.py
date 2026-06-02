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

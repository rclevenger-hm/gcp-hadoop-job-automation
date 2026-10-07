import json

import pytest
from app.config import load_profiles
from app.validation import ApiError, body, integer, job_request
from conftest import CALLER, OTHER


def test_oci_four_fields_map_to_dataproc_with_profile(payload, profiles):
    assert job_request(payload, profiles, CALLER) == payload


@pytest.mark.parametrize('field,value', [('job_class', 'org.Job;rm'), ('job_class', 'bad class'), ('jar_path', 'gs://elsewhere/job.jar'), ('input_path', 'gs://your-data/input/../secret'), ('input_path', 'gs://your-data/input/%2e%2e/x'), ('input_path', 'gs://your-data/input/x\n'), ('output_path', 'gs://your-data/outputx/file'), ('jar_path', None), ('arguments', 'x'), ('arguments', ['x'] * 21), ('arguments', ['x' * 1025]), ('job_class', '\ud800')])
def test_invalid_fields_fail_before_execution(payload, profiles, field, value):
    payload[field] = value
    with pytest.raises(ApiError):
        job_request(payload, profiles, CALLER)


def test_java_arguments_are_data_not_shell(payload, profiles):
    payload['arguments'] = ['$(touch /tmp/owned)', 'two words', 'a; b']
    assert job_request(payload, profiles, CALLER)['arguments'] == payload['arguments']


def test_profile_authorization(payload, profiles):
    with pytest.raises(ApiError, match='not authorized'):
        job_request(payload, profiles, OTHER)


def test_unknown_request_fields_are_rejected(payload, profiles):
    payload['execution_role_arn'] = 'attacker'
    with pytest.raises(ApiError, match='Unknown'):
        job_request(payload, profiles, CALLER)


def test_aggregate_job_limit(payload, profiles):
    payload['arguments'] = ['x' * 1024] * 10
    with pytest.raises(ApiError, match='10240'):
        job_request(payload, profiles, CALLER)


def test_utf8_body():
    assert body(json.dumps({'text': '雪'}).encode()) == {'text': '雪'}


@pytest.mark.parametrize('raw', [b'null', b'[]', b'NaN', b'{', b'{"x":NaN}', b'\xff'])
def test_invalid_json_envelopes(raw):
    with pytest.raises(ApiError):
        body(raw)


def test_body_size():
    with pytest.raises(ApiError) as error:
        body(b'x' * 65537)
    assert error.value.status == 413


@pytest.mark.parametrize('value', ['-1', '0', '101', '1.2', 'NaN'])
def test_pagination_bounds(value):
    with pytest.raises(ApiError):
        integer(value, 20, 100)


@pytest.mark.parametrize('field,value', [('cluster_name', 'Invalid_CLUSTER'), ('allowed_callers', ['*']), ('jar_prefixes', ['gs://bucket/root']), ('log_prefixes', ['https://attacker/']), ('jar_prefixes', ['gs://bucket/root/../']), ('input_prefixes', ['gs://bucket/root/*/'])])
def test_bad_configuration_fails_closed(profiles, field, value):
    profiles['analytics'][field] = value
    with pytest.raises(ValueError):
        load_profiles(json.dumps(profiles))

import base64
import json

import pytest
from flask import Flask, request

from app import handlers
from app.validation import ApiError
from conftest import CALLER, create, message


@pytest.fixture
def http(env, monkeypatch):
    monkeypatch.setattr(handlers, 'runtime', lambda: env.service)
    monkeypatch.setattr(handlers, 'authenticate', lambda *a: CALLER)
    monkeypatch.setenv('TOKEN_AUDIENCE', 'https://example.com')
    monkeypatch.setenv('ALLOWED_CALLER_EMAILS', CALLER.email)
    app = Flask(__name__)
    def call(path='/jobs', method='POST', value=None, handler=handlers.api_handler, **kwargs):
        with app.test_request_context(path, method=method, json=value, headers={'Idempotency-Key': 'valid-key-123'}, **kwargs):
            return handler(request)
    return call


def test_create_replay_history_and_usage(http, payload):
    raw, status, headers = http(value=payload)
    job = json.loads(raw)
    assert status == 202 and headers['Cache-Control'] == 'no-store'
    assert http(value=payload)[1] == 200
    assert json.loads(http('/jobs', 'GET')[0])['jobs'][0]['job_id'] == job['job_id']
    assert json.loads(http('/usage', 'GET')[0])['jobs'] == 1
    assert http('/jobs/' + job['job_id'], 'GET')[1] == 200
    assert http('/jobs/' + job['job_id'] + '/cancel')[1] == 200


def test_auth_before_runtime_or_body(http, monkeypatch):
    def deny(*args):
        raise ApiError(401, 'UNAUTHENTICATED', 'Denied')
    monkeypatch.setattr(handlers, 'authenticate', deny)
    monkeypatch.setattr(handlers, 'runtime', lambda: pytest.fail('must authenticate first'))
    assert http(value={'anything': True})[1] == 401


def test_errors_do_not_expose_request_or_provider_data(http, env, payload):
    env.publisher.publish.side_effect = RuntimeError('SECRET-TOKEN')
    result = http(value=payload)
    assert result[1] == 503 and 'SECRET-TOKEN' not in result[0]


@pytest.mark.parametrize('path', ['/unknown', '/jobs/no-such-job', '/jobs?status=UNKNOWN', '/jobs?limit=0'])
def test_invalid_routes_queries(http, path):
    assert http(path, 'GET')[1] in {400, 404}


def test_body_and_content_type_bounds(http):
    assert http(value={'text': 'x' * 65537})[1] == 413
    assert http()[1] == 415


def test_worker_valid_duplicate_and_malformed(http, env, payload):
    job = create(env, payload)
    encoded = base64.b64encode(json.dumps(message(job)).encode()).decode()
    envelope = {'message': {'data': encoded}}
    assert http(value=envelope, handler=handlers.worker_handler)[1] == 204
    assert http(value=envelope, handler=handlers.worker_handler)[1] == 204
    env.dp.submit.assert_called_once()
    assert http(value={'message': {'data': '!'}}, handler=handlers.worker_handler)[1] == 503
    assert http(method='GET', handler=handlers.worker_handler)[1] == 405

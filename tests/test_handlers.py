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

import time
from types import SimpleNamespace
from unittest.mock import Mock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth import authenticate
from app.validation import ApiError
from conftest import CALLER


@pytest.fixture
def signed():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    claims = {'iss': 'https://accounts.google.com', 'sub': CALLER.subject, 'email': CALLER.email,
              'email_verified': True, 'aud': 'https://service.example', 'iat': int(time.time()), 'exp': int(time.time()) + 600}
    keys = Mock()
    keys.get_signing_key_from_jwt.return_value = SimpleNamespace(key=private.public_key())
    return private, claims, keys


def invoke(signed):
    private, claims, keys = signed
    return authenticate('Bearer ' + jwt.encode(claims, private, algorithm='RS256'), 'https://service.example', {CALLER.email}, keys)


def test_valid_google_identity(signed):
    assert invoke(signed) == CALLER
    signed[1]['iss'] = 'accounts.google.com'
    assert invoke(signed).tenant == CALLER.tenant


@pytest.mark.parametrize('field,value', [('iss', 'attacker'), ('aud', 'other'), ('exp', 0), ('iat', 9999999999), ('sub', 'email@example.com'), ('email_verified', False), ('email', 'other@example.com')])
def test_wrong_claims_fail_closed(signed, field, value):
    signed[1][field] = value
    with pytest.raises(ApiError) as error:
        invoke(signed)
    assert error.value.status == 401


def test_wrong_signature_rejected(signed):
    signed[2].get_signing_key_from_jwt.return_value.key = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    with pytest.raises(ApiError):
        invoke(signed)


@pytest.mark.parametrize('header', [None, '', 'Basic fake', 'Bearer ' + 'x' * 17000])
def test_missing_or_oversized_token(header):
    with pytest.raises(ApiError):
        authenticate(header, 'audience', {CALLER.email})

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

import re
from dataclasses import dataclass

import jwt

from app.validation import ApiError, digest

ISSUERS = ['https://accounts.google.com', 'accounts.google.com']
JWKS = jwt.PyJWKClient('https://www.googleapis.com/oauth2/v3/certs', cache_keys=True, lifespan=300, timeout=5)


@dataclass(frozen=True)
class Identity:
    subject: str
    email: str

    @property
    def tenant(self):
        return digest(f'https://accounts.google.com:{self.subject}')


def authenticate(header, audience, allowed, key_client=JWKS):
    try:
        if not isinstance(header, str) or not header.startswith('Bearer ') or len(header) > 16384:
            raise ValueError()
        token = header[7:]
        key = key_client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=['RS256'], audience=audience, issuer=ISSUERS,
                            options={'require': ['exp', 'iat', 'sub', 'email', 'iss', 'aud']})
        if not re.fullmatch(r'[0-9]{1,255}', claims['sub']) or claims.get('email_verified') is not True or claims['email'] not in allowed:
            raise ValueError()
        return Identity(claims['sub'], claims['email'])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as exc:
        raise ApiError(401, 'UNAUTHENTICATED', 'A verified, authorized Google service account ID token is required') from exc

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

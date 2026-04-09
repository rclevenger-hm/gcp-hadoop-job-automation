import hashlib
import json
import re
from urllib.parse import urlsplit

MAX_BODY = 65536
TERMINAL = frozenset({'SUCCEEDED', 'FAILED', 'CANCELLED', 'NEEDS_REVIEW'})
STATES = TERMINAL | {'QUEUED', 'SUBMITTING', 'SUBMISSION_UNKNOWN', 'SUBMITTED', 'RUNNING', 'CANCEL_REQUESTED'}


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code = status, code


def invalid(message):
    return ApiError(400, 'INVALID_REQUEST', message)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def body(raw):
    if not isinstance(raw, bytes):
        raise invalid('A JSON body is required')
    if len(raw) > MAX_BODY:
        raise ApiError(413, 'BODY_TOO_LARGE', 'Body exceeds 64 KiB')
    try:
        result = json.loads(raw.decode('utf-8'), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError) as exc:
        raise invalid('Body must be valid UTF-8 JSON') from exc
    if not isinstance(result, dict):
        raise invalid('Body must be a JSON object')
    return result


def text(value, field, maximum=4096):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise invalid(f'{field} must be nonblank text, at most {maximum} characters, without controls')
    try:
        value.encode('utf-8')
    except UnicodeError as exc:
        raise invalid(f'{field} must be valid Unicode') from exc
    return value.strip()


def allowed_path(value, prefixes, field):
    value = text(value, field)
    try:
        parts = urlsplit(value)
    except ValueError as exc:
        raise invalid(f'{field} is not a valid URI') from exc
    if parts.scheme not in {'gs', 'hdfs'} or parts.query or parts.fragment or '%' in value or '\\' in value or any(p in {'.', '..'} for p in parts.path.split('/')):
        raise invalid(f'{field} must be a canonical GCS or HDFS URI')
    if not any(value.startswith(p) and len(value) > len(p) for p in prefixes):
        raise ApiError(403, 'PATH_NOT_ALLOWED', f'{field} is outside the configured prefixes')
    return value

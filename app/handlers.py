import base64
import json
import os
import re
import time
import uuid

from google.cloud import dataproc_v1, firestore, pubsub_v1, storage

from app.auth import authenticate
from app.config import settings
from app.dataproc import Dataproc, RemoteMismatch
from app.service import Service, public
from app.store import Store
from app.validation import ApiError, MAX_BODY, STATES, body, integer

_SERVICE = None


def runtime():
    global _SERVICE
    if _SERVICE is None:
        cfg = settings()
        db = firestore.Client(project=cfg['project'], database=cfg['database'])
        store = Store(db, pubsub_v1.PublisherClient(), cfg['topic'], cfg['daily_limit'], cfg['rate_limit'], cfg['retention'])
        client = dataproc_v1.JobControllerClient(client_options={'api_endpoint': f"{cfg['region']}-dataproc.googleapis.com:443"})
        _SERVICE = Service(store, Dataproc(client, storage.Client(project=cfg['project']), cfg['project'], cfg['region']), cfg['profiles'], cfg['prefix'])
    return _SERVICE


def response(status, value, request_id):
    return json.dumps(value), status, {'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Request-Id': request_id,
                                     **({'Retry-After': '60'} if status == 429 else {})}


def api_handler(request):
    request_id, status = str(uuid.uuid4()), 500
    try:
        caller = authenticate(request.headers.get('Authorization'), os.environ['TOKEN_AUDIENCE'], os.environ['ALLOWED_CALLER_EMAILS'].split(','))
        service = runtime()
        service.store.request_limit(caller.tenant)
        method, path, query = request.method, request.path.rstrip('/') or '/', request.args
        match = re.fullmatch(r'/jobs/([^/]+)(?:/(cancel|logs))?', path)
        result, status = None, 200
        if method == 'POST' and path == '/jobs':
            if request.mimetype != 'application/json':
                raise ApiError(415, 'UNSUPPORTED_MEDIA_TYPE', 'Use application/json')
            if request.content_length is not None and request.content_length > MAX_BODY:
                raise ApiError(413, 'BODY_TOO_LARGE', 'Body exceeds 64 KiB')
            result, created = service.submit(caller, request.headers.get('Idempotency-Key'), body(request.stream.read(MAX_BODY + 1)))
            status = 202 if created else 200
        elif method == 'GET' and path == '/jobs':
            if query.get('status') and query['status'] not in STATES:
                raise ApiError(400, 'INVALID_STATUS', 'Unknown job status')
            jobs, cursor = service.store.history(caller.tenant, integer(query.get('limit'), 20, 100), query.get('cursor'), query.get('status'))
            result = {'jobs': [public(j) for j in jobs], 'next_cursor': cursor}
        elif method == 'GET' and match and not match[2]:
            result = public(service.owned(caller, match[1]))
        elif method == 'POST' and match and match[2] == 'cancel':
            result = service.cancel(caller, match[1])
            status = 202 if result['status'] == 'CANCEL_REQUESTED' else 200
        elif method == 'GET' and match and match[2] == 'logs':
            result = service.dataproc.logs(service.owned(caller, match[1]), query.get('stream', 'driver'), integer(query.get('limit'), 16384, 65536), query.get('segment', '0'), query.get('offset', '0'))
        elif method == 'GET' and path == '/usage':
            result = service.store.usage(caller.tenant)
        else:
            raise ApiError(404, 'NOT_FOUND', 'Route not found')
        return response(status, result, request_id)
    except ApiError as exc:
        status = exc.status
        result = response(status, {'code': exc.code, 'error': str(exc), 'request_id': request_id}, request_id)
        if exc.code == 'DAILY_LIMIT':
            result[2]['Retry-After'] = str(86400 - int(time.time()) % 86400)
        return result
    except RemoteMismatch:
        status = 409
        return response(status, {'code': 'REMOTE_IDENTITY_MISMATCH', 'error': 'Remote job requires operator review'}, request_id)
    except Exception as exc:
        status = 503
        print(json.dumps({'event': 'api_error', 'request_id': request_id, 'error_type': type(exc).__name__}), flush=True)
        return response(status, {'code': 'SERVICE_UNAVAILABLE', 'error': 'Service temporarily unavailable', 'request_id': request_id}, request_id)
    finally:
        print(json.dumps({'event': 'api_request', 'request_id': request_id, 'status': status}), flush=True)

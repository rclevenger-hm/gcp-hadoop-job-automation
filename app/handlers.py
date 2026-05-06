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

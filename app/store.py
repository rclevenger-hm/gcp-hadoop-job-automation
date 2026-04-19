import base64
import json
import time
import uuid
from datetime import datetime, timezone

from google.api_core.retry import Retry
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.validation import ApiError, TERMINAL, canonical, digest, identifier, invalid


def expires(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc)


class Store:
    def __init__(self, db, publisher, topic, daily_limit=100, rate_limit=60, retention=30, clock=time.time, transaction_runner=None):
        self.db, self.items, self.publisher, self.topic = db, db.collection('items'), publisher, topic
        self.daily_limit, self.rate_limit, self.retention, self.clock = daily_limit, rate_limit, retention, clock
        self.transaction_runner = transaction_runner
        if not all(isinstance(v, int) and v > 0 for v in [daily_limit, rate_limit, retention]):
            raise ValueError('Limits must be positive integers')

    def transaction(self, callback):
        if self.transaction_runner:
            return self.transaction_runner(callback)
        return firestore.transactional(callback)(self.db.transaction(max_attempts=8))

    def now(self):
        return int(self.clock())

    def date(self):
        return datetime.fromtimestamp(self.now(), timezone.utc).strftime('%Y-%m-%d')

    def ref(self, tenant, job_id):
        return self.items.document(digest(f'{tenant}:{job_id}'))

    def counter(self, tenant, period):
        return self.items.document(digest(f'counter:{tenant}:{period}'))

    def get(self, tenant, job_id):
        item = self.ref(tenant, job_id).get(timeout=8).to_dict()
        if item and item.get('expires_at', self.now() + 1) > self.now():
            return item
        return None

    def enqueue(self, job):
        data = canonical({'tenant': job['tenant'], 'job_id': job['job_id']}).encode()
        self.publisher.publish(self.topic, data=data, retry=Retry(deadline=8)).result(timeout=10)

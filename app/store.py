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

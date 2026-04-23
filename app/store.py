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

    def decorate(self, job):
        if job['status'] in TERMINAL:
            job.pop('active_shard', None)
            job['expires_at'] = self.now() + self.retention * 86400
            job['expiresOn'] = expires(job['expires_at'])
        else:
            job.pop('expires_at', None)
            job.pop('expiresOn', None)
            job['active_shard'] = job['job_id'][0]
        return job

    def create(self, tenant, job_id, request, profile, prefix):
        fingerprint, submission_id = digest(canonical(request)), str(uuid.uuid4())
        job = self.decorate({'tenant': tenant, 'kind': 'job', 'job_id': job_id, 'request': request, 'profile': profile,
                             'fingerprint': fingerprint, 'submission_id': submission_id,
                             'dataproc_job_id': f'{prefix}-{job_id[:16]}-{submission_id.replace("-", "")}',
                             'status': 'QUEUED', 'version': 1, 'attempts': 0,
                             'created_at': self.now(), 'updated_at': self.now(), 'next_check': self.now() + 120})
        ref, usage_ref = self.ref(tenant, job_id), self.counter(tenant, self.date())
        def admit(tx):
            existing = ref.get(transaction=tx).to_dict()
            usage = usage_ref.get(transaction=tx).to_dict() or {}
            if existing:
                if existing.get('expires_at', self.now() + 1) <= self.now():
                    raise ApiError(409, 'EXPIRED_KEY', 'Use a fresh idempotency key')
                if existing['fingerprint'] != fingerprint:
                    raise ApiError(409, 'IDEMPOTENCY_CONFLICT', 'Key already used with different job inputs')
                return existing, False
            if usage.get('units', 0) >= self.daily_limit:
                raise ApiError(429, 'DAILY_LIMIT', 'Daily job allowance exhausted')
            tx.create(ref, job)
            tx.set(usage_ref, {'units': usage.get('units', 0) + 1, 'expiresOn': expires(self.now() + 3 * 86400)})
            return job, True
        return self.transaction(admit)

    def replace(self, job, **changes):
        ref = self.ref(job['tenant'], job['job_id'])
        updated = self.decorate({**job, **changes, 'version': job['version'] + 1, 'updated_at': self.now()})
        def compare(tx):
            current = ref.get(transaction=tx).to_dict()
            if not current or current['version'] != job['version'] or current.get('expires_at', self.now() + 1) <= self.now():
                return None
            tx.set(ref, updated)
            return updated
        result = self.transaction(compare)
        if result and result['status'] != job['status']:
            print(json.dumps({'event': 'job_state', 'job_id': job['job_id'], 'status': result['status']}), flush=True)
        return result

    def request_limit(self, tenant):
        ref = self.counter(tenant, f'rate:{self.now() // 60}')
        def increment(tx):
            old = ref.get(transaction=tx).to_dict() or {}
            if old.get('units', 0) >= self.rate_limit:
                raise ApiError(429, 'RATE_LIMIT', 'Request allowance exhausted; retry in one minute')
            tx.set(ref, {'units': old.get('units', 0) + 1, 'expiresOn': expires(self.now() + 120)})
        self.transaction(increment)

    def usage(self, tenant):
        item = self.counter(tenant, self.date()).get(timeout=8).to_dict() or {}
        return {'date': self.date(), 'jobs': item.get('units', 0), 'limit': self.daily_limit}

    def history(self, tenant, limit=20, cursor=None, status=None):
        signature = digest(canonical({'tenant': tenant, 'status': status}))
        query = self.items.where(filter=FieldFilter('tenant', '==', tenant)).where(filter=FieldFilter('kind', '==', 'job'))
        if status:
            query = query.where(filter=FieldFilter('status', '==', status))
        query = query.order_by('created_at', direction='DESCENDING').order_by('__name__', direction='DESCENDING')
        if cursor:
            try:
                if len(cursor) > 2048:
                    raise ValueError()
                decoded = json.loads(base64.b64decode(cursor, altchars=b'-_', validate=True))
                if decoded['signature'] != signature or not isinstance(decoded['created_at'], int):
                    raise ValueError()
                query = query.start_after({'created_at': decoded['created_at'], '__name__': self.items.document(identifier(decoded['id']))})
            except (ValueError, KeyError, TypeError, ApiError) as exc:
                raise invalid('Cursor does not match this query') from exc
        rows = list(query.limit(limit + 1).stream(timeout=8))
        scanned = rows[:limit]
        jobs = [row.to_dict() for row in scanned]
        jobs = [j for j in jobs if j.get('expires_at', self.now() + 1) > self.now()]
        token = None
        if len(rows) > limit:
            last = scanned[-1]
            token = base64.urlsafe_b64encode(canonical({'signature': signature, 'created_at': last.to_dict()['created_at'], 'id': last.id}).encode()).decode()
        return jobs, token

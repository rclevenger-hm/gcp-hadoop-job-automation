from app.dataproc import RemoteMismatch
from app.validation import ApiError, TERMINAL, identifier, job_request, key_id


def public(job):
    fields = ['job_id', 'status', 'created_at', 'updated_at', 'dataproc_job_id', 'cancel_requested', 'cancel_accepted', 'reason', 'expires_at']
    return {**{k: job[k] for k in fields if k in job}, 'profile': job['request']['profile']}


class Service:
    def __init__(self, store, dataproc, profiles, prefix):
        self.store, self.dataproc, self.profiles, self.prefix = store, dataproc, profiles, prefix

    def submit(self, caller, key, payload):
        request = job_request(payload, self.profiles, caller)
        job_id = key_id(key, caller.tenant)
        job, created = self.store.create(caller.tenant, job_id, request, self.profiles[request['profile']], self.prefix)
        if job['status'] == 'QUEUED':
            self.store.enqueue(job)
        return public(job), created

    def owned(self, caller, job_id):
        job = self.store.get(caller.tenant, identifier(job_id))
        if not job:
            raise ApiError(404, 'NOT_FOUND', 'Job not found')
        return job

    def cancel(self, caller, job_id):
        for _ in range(4):
            job = self.owned(caller, job_id)
            if job['status'] == 'CANCELLED' or job.get('cancel_requested'):
                return public(job)
            if job['status'] in TERMINAL:
                raise ApiError(409, 'ALREADY_FINISHED', 'This job is no longer accepting cancellation')
            safe = job['status'] == 'QUEUED' and job['attempts'] == 0
            updated = self.store.replace(job, status='CANCELLED' if safe else 'CANCEL_REQUESTED', cancel_requested=True, next_check=self.store.now())
            if updated:
                return public(updated)
        raise ApiError(409, 'STATE_CHANGED', 'Job changed concurrently; retry the request')

    def attach(self, tenant, job_id, remote=None, reason='SUBMISSION_OUTCOME_UNKNOWN'):
        for _ in range(5):
            job = self.store.get(tenant, job_id)
            if not job or job['status'] in TERMINAL or job.get('remote_uuid'):
                return
            changes = {'next_check': self.store.now() + 120}
            if remote is not None:
                self.dataproc.verify(job, remote)
                changes.update(remote_uuid=remote.job_uuid, status='CANCEL_REQUESTED' if job.get('cancel_requested') else 'SUBMITTED', reason='')
            else:
                changes.update(status='CANCEL_REQUESTED' if job.get('cancel_requested') else 'SUBMISSION_UNKNOWN', reason=reason)
            if self.store.replace(job, **changes):
                return
        raise RuntimeError('Concurrent updates prevented attachment; reconciliation will retry')

    def expire_queued(self, job):
        if self.store.now() - job['created_at'] < 86400:
            return False
        self.store.replace(job, status='NEEDS_REVIEW' if job['attempts'] else 'FAILED', reason='ADMISSION_WINDOW_EXPIRED')
        return True

    def process(self, message):
        tenant, job_id = identifier(message.get('tenant')), identifier(message.get('job_id'))
        job = self.store.get(tenant, job_id)
        if not job or job['status'] != 'QUEUED' or self.expire_queued(job):
            return
        job = self.store.replace(job, status='SUBMITTING', submitted_at=self.store.now(), attempts=job['attempts'] + 1, next_check=self.store.now() + 120)
        if not job:
            return
        try:
            remote = self.dataproc.submit(job)
        except RemoteMismatch:
            self.review(tenant, job_id, 'REMOTE_IDENTITY_MISMATCH')
            return
        except Exception:
            self.attach(tenant, job_id)
            return
        self.attach(tenant, job_id, remote)

    def review(self, tenant, job_id, reason):
        for _ in range(5):
            job = self.store.get(tenant, job_id)
            if not job or job['status'] in TERMINAL:
                return
            if self.store.replace(job, status='NEEDS_REVIEW', reason=reason):
                return
        raise RuntimeError('Concurrent updates prevented review marker')

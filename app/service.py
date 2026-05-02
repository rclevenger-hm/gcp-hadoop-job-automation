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

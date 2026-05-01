from app.dataproc import RemoteMismatch
from app.validation import ApiError, TERMINAL, identifier, job_request, key_id


def public(job):
    fields = ['job_id', 'status', 'created_at', 'updated_at', 'dataproc_job_id', 'cancel_requested', 'cancel_accepted', 'reason', 'expires_at']
    return {**{k: job[k] for k in fields if k in job}, 'profile': job['request']['profile']}


class Service:
    def __init__(self, store, dataproc, profiles, prefix):
        self.store, self.dataproc, self.profiles, self.prefix = store, dataproc, profiles, prefix

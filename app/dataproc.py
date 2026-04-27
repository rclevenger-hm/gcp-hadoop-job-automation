from urllib.parse import urlsplit

from google.api_core.exceptions import AlreadyExists, NotFound, RequestRangeNotSatisfiable
from google.cloud import dataproc_v1

from app.validation import ApiError, allowed_path, integer, invalid

STATE_MAP = {'PENDING': 'SUBMITTED', 'SETUP_DONE': 'SUBMITTED', 'RUNNING': 'RUNNING',
             'ATTEMPT_FAILURE': 'RUNNING', 'CANCEL_PENDING': 'CANCEL_REQUESTED',
             'CANCEL_STARTED': 'CANCEL_REQUESTED', 'DONE': 'SUCCEEDED', 'ERROR': 'FAILED', 'CANCELLED': 'CANCELLED'}


class RemoteMismatch(Exception):
    """The remote ID no longer refers to the admitted job."""


class Dataproc:
    def __init__(self, client, storage, project, region):
        self.client, self.storage, self.project, self.region = client, storage, project, region

    def locator(self, job):
        return {'project_id': self.project, 'region': self.region, 'job_id': job['dataproc_job_id']}

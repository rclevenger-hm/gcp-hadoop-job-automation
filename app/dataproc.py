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

    @staticmethod
    def hadoop(job):
        r = job['request']
        return {'main_class': r['job_class'], 'jar_file_uris': [r['jar_path']],
                'args': [r['input_path'], r['output_path'], *r['arguments']]}

    def verify(self, job, remote):
        hadoop = self.hadoop(job)
        if (remote.reference.project_id != self.project or remote.reference.job_id != job['dataproc_job_id']
                or remote.placement.cluster_name != job['profile']['cluster_name']
                or remote.labels.get('submission') != job['submission_id']
                or remote.hadoop_job.main_class != hadoop['main_class']
                or list(remote.hadoop_job.jar_file_uris) != hadoop['jar_file_uris']
                or list(remote.hadoop_job.args) != hadoop['args']
                or not remote.job_uuid or (job.get('remote_uuid') and remote.job_uuid != job['remote_uuid'])):
            raise RemoteMismatch('Remote job identity mismatch')
        return remote

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

    def submit(self, job):
        request = {'project_id': self.project, 'region': self.region, 'request_id': job['submission_id'],
                   'job': {'reference': {'project_id': self.project, 'job_id': job['dataproc_job_id']},
                           'placement': {'cluster_name': job['profile']['cluster_name']},
                           'hadoop_job': self.hadoop(job), 'labels': {'submission': job['submission_id']}}}
        # No restartable-job scheduling: each admitted Hadoop job is submitted once logically.
        # App retries reuse the exact native request ID and job ID, including after transport errors.
        try:
            remote = self.client.submit_job(request=request, retry=None, timeout=10)
        except AlreadyExists:
            remote = self.client.get_job(request=self.locator(job), retry=None, timeout=10)
        return self.verify(job, remote)

    def get(self, job):
        try:
            return self.verify(job, self.client.get_job(request=self.locator(job), retry=None, timeout=10))
        except NotFound:
            return None

    @staticmethod
    def state(remote):
        name = dataproc_v1.JobStatus.State(remote.status.state).name
        if name not in STATE_MAP:
            raise RuntimeError('Unrecognized Dataproc state')
        return STATE_MAP[name]

    def cancel(self, job):
        # Fence a deleted/reused job ID immediately before cancellation.
        remote = self.get(job)
        if remote is None:
            raise RemoteMismatch('Remote job disappeared before cancellation')
        result = self.client.cancel_job(request=self.locator(job), retry=None, timeout=10)
        self.verify(job, result)
        return True

    def logs(self, job, stream='driver', limit=16384, segment='0', offset='0'):
        if stream != 'driver':
            raise invalid('Only the Dataproc driver stream is available')
        limit = integer(limit, 16384, 65536)
        try:
            if not str(segment).isdigit() or not str(offset).isdigit() or len(str(segment)) > 6 or len(str(offset)) > 9:
                raise ValueError()
            segment, offset = int(segment), int(offset)
            if not 0 <= segment <= 999999 or not 0 <= offset <= 104857600:
                raise ValueError()
        except (ValueError, TypeError) as exc:
            raise invalid('Invalid driver segment or byte offset') from exc
        remote = self.get(job)
        if remote is None or not remote.driver_output_resource_uri:
            raise ApiError(404, 'LOG_NOT_READY', 'Driver output is not available yet')
        uri = urlsplit(allowed_path(remote.driver_output_resource_uri, job['profile']['log_prefixes'], 'driver output'))
        blob = self.storage.bucket(uri.netloc).blob(f'{uri.path.lstrip("/")}.{segment:09d}')
        try:
            raw = blob.download_as_bytes(start=offset, end=offset + limit, raw_download=True, retry=None, timeout=8)
        except NotFound as exc:
            raise ApiError(404, 'LOG_NOT_READY', 'Driver output segment has not been uploaded') from exc
        except RequestRangeNotSatisfiable:
            raw = b''
        return {'stream': 'driver', 'segment': segment, 'offset': offset, 'text': raw[:limit].decode('utf-8', errors='replace'),
                'truncated': len(raw) > limit, 'next_offset': offset + limit if len(raw) > limit else None,
                'note': 'Output can lag execution. At segment end, retry later or request the next segment.'}

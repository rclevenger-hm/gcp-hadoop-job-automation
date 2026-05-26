import copy
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.cloud import dataproc_v1

from app.auth import Identity
from app.config import load_profiles
from app.dataproc import Dataproc
from app.service import Service
from app.store import Store
from fakes import Database

CALLER = Identity('123456789', 'hadoop-consumer@your-project-id.iam.gserviceaccount.com')
OTHER = Identity('987654321', 'other@your-project-id.iam.gserviceaccount.com')


@pytest.fixture
def profiles():
    return load_profiles(open('examples/profiles.json').read())


@pytest.fixture
def payload():
    return json.load(open('examples/job.json'))


def remote(job, state='RUNNING', uuid='remote-unique-id'):
    return dataproc_v1.Job(reference={'project_id': 'your-project-id', 'job_id': job['dataproc_job_id']},
                           placement={'cluster_name': job['profile']['cluster_name']}, labels={'submission': job['submission_id']},
                           hadoop_job=Dataproc.hadoop(job), status={'state': state}, job_uuid=uuid,
                           driver_output_resource_uri='gs://your-staging/google-cloud-dataproc-metainfo/cluster/jobs/job/driveroutput')


@pytest.fixture
def env(profiles):
    db, publisher, client, storage = Database(), Mock(), Mock(), Mock()
    clock = [1780315200]
    store = Store(db, publisher, 'projects/your-project-id/topics/jobs', clock=lambda: clock[0], transaction_runner=db.run)
    native = Dataproc(client, storage, 'your-project-id', 'us-central1')
    dp = Mock(wraps=native)
    dp.submit.side_effect = remote
    dp.get.side_effect = remote
    dp.cancel.return_value = True
    service = Service(store, dp, copy.deepcopy(profiles), 'hadoop-dev')
    return SimpleNamespace(store=store, service=service, dp=dp, native=native, client=client, storage=storage, clock=clock, db=db, publisher=publisher)

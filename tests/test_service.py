import pytest
from app.dataproc import RemoteMismatch
from app.validation import ApiError
from conftest import CALLER, OTHER, create, message, remote


def test_duplicate_deliveries_submit_once(env, payload):
    job = create(env, payload)
    env.service.process(message(job))
    env.service.process(message(job))
    env.dp.submit.assert_called_once()
    assert env.store.get(job['tenant'], job['job_id'])['remote_uuid'] == 'remote-unique-id'

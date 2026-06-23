import copy
from concurrent.futures import ThreadPoolExecutor

import pytest
from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.validation import ApiError
from app.store import Store
from conftest import CALLER, OTHER, create


def test_replay_does_not_charge_twice(env, payload):
    first = create(env, payload)
    second = create(env, payload)
    assert first['submission_id'] == second['submission_id']
    assert env.store.usage(CALLER.tenant)['jobs'] == 1


def test_conflicting_payload_is_rejected(env, payload):
    create(env, payload)
    payload['job_class'] = 'org.Different'
    with pytest.raises(ApiError, match='different'):
        create(env, payload)


def test_concurrent_admission_is_atomic(env, payload):
    with ThreadPoolExecutor(max_workers=10) as executor:
        jobs = list(executor.map(lambda _: create(env, copy.deepcopy(payload)), range(30)))
    assert len({j['submission_id'] for j in jobs}) == 1
    assert env.store.usage(CALLER.tenant)['jobs'] == 1

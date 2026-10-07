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


def test_quota_rejects_new_job_but_allows_replay(env, payload):
    env.store.daily_limit = 1
    first = create(env, payload)
    assert create(env, payload)['job_id'] == first['job_id']
    with pytest.raises(ApiError, match='exhausted'):
        create(env, payload, 'different-key')
    assert len(env.store.history(CALLER.tenant)[0]) == 1


def test_rate_limit_and_next_window(env):
    env.store.rate_limit = 2
    env.store.request_limit(CALLER.tenant)
    env.store.request_limit(CALLER.tenant)
    with pytest.raises(ApiError, match='exhausted'):
        env.store.request_limit(CALLER.tenant)
    env.clock[0] += 60
    env.store.request_limit(CALLER.tenant)


def test_compare_and_swap_prevents_lost_cancellation(env, payload):
    job = create(env, payload)
    cancelled = env.store.replace(job, status='CANCELLED', cancel_requested=True)
    assert env.store.replace(job, status='RUNNING') is None
    assert env.store.get(CALLER.tenant, job['job_id']) == cancelled


def test_active_jobs_never_ttl_and_terminal_jobs_do(env, payload):
    job = create(env, payload)
    assert 'expiresOn' not in job
    final = env.store.replace(job, status='SUCCEEDED')
    assert 'active_shard' not in final
    assert final['expiresOn'].timestamp() == final['expires_at']
    env.clock[0] = final['expires_at']
    assert env.store.get(CALLER.tenant, job['job_id']) is None
    with pytest.raises(ApiError, match='fresh'):
        create(env, payload)


def test_reused_key_after_ttl_gets_new_remote_ids(env, payload):
    job = create(env, payload)
    del env.db.data[env.store.ref(CALLER.tenant, job['job_id']).id]
    new = create(env, payload)
    assert new['job_id'] == job['job_id']
    assert new['dataproc_job_id'] != job['dataproc_job_id']
    assert new['submission_id'] != job['submission_id']


def test_history_pagination_status_filter_and_tenant_fence(env, payload):
    jobs = [create(env, payload, f'key-number-{i}') for i in range(5)]
    for j in jobs[:3]:
        env.store.replace(j, status='SUCCEEDED')
    first, token = env.store.history(CALLER.tenant, 2, status='SUCCEEDED')
    second, end = env.store.history(CALLER.tenant, 2, token, 'SUCCEEDED')
    assert len(first) == 2 and len(second) == 1 and end is None
    assert len({j['job_id'] for j in first + second}) == 3
    for tenant, status in [(OTHER.tenant, 'SUCCEEDED'), (CALLER.tenant, 'RUNNING')]:
        with pytest.raises(ApiError, match='Cursor'):
            env.store.history(tenant, 2, token, status)


@pytest.mark.parametrize('cursor', ['!', 'a' * 2049, 'e30='])
def test_bad_history_cursor(env, cursor):
    with pytest.raises(ApiError):
        env.store.history(CALLER.tenant, cursor=cursor)


def test_claim_poll_lease_excludes_duplicate_worker(env, payload):
    job = create(env, payload)
    assert env.store.claim_poll(CALLER.tenant, job['job_id']) is None
    env.clock[0] += 121
    assert env.store.claim_poll(CALLER.tenant, job['job_id']) is not None
    assert env.store.claim_poll(CALLER.tenant, job['job_id']) is None


def test_expired_history_records_are_hidden(env, payload):
    job = create(env, payload)
    env.store.replace(job, status='FAILED')
    env.clock[0] += 31 * 86400
    assert env.store.history(CALLER.tenant)[0] == []


def test_sdk_query_cursor_shapes_without_network():
    db = firestore.Client(project='test-project', credentials=AnonymousCredentials())
    query = db.collection('items').where(filter=FieldFilter('tenant', '==', 'test')).order_by('created_at', direction='DESCENDING').order_by('__name__', direction='DESCENDING')
    wire = query.start_after({'created_at': 123, '__name__': db.collection('items').document('a' * 64)})._to_protobuf()
    assert len(wire.start_at.values) == 2
    assert wire.start_at.values[1].reference_value.endswith('/items/' + 'a' * 64)
    assert callable(Store(db, None, '').transaction)

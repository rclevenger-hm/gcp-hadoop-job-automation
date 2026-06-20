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

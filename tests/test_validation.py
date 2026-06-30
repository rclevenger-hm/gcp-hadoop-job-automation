import json

import pytest
from app.config import load_profiles
from app.validation import ApiError, body, integer, job_request
from conftest import CALLER, OTHER


def test_oci_four_fields_map_to_dataproc_with_profile(payload, profiles):
    assert job_request(payload, profiles, CALLER) == payload

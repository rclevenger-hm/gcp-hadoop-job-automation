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

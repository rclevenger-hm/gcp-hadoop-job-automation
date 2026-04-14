import base64
import json
import time
import uuid
from datetime import datetime, timezone

from google.api_core.retry import Retry
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.validation import ApiError, TERMINAL, canonical, digest, identifier, invalid


def expires(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc)

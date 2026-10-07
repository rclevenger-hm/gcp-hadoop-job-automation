import json
import os
import re
from urllib.parse import urlsplit


def load_profiles(raw):
    profiles = json.loads(raw)
    if not isinstance(profiles, dict) or not 1 <= len(profiles) <= 5 or len(raw.encode()) > 16000:
        raise ValueError('Configure one to five profiles within 16 KiB')
    for name, p in profiles.items():
        if not re.fullmatch(r'[a-z][a-z0-9-]{2,39}', name) or not isinstance(p, dict):
            raise ValueError('Invalid cluster profile')
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,49}[a-z0-9]', p.get('cluster_name', '')):
            raise ValueError('Invalid Dataproc cluster name')
        callers = p.get('allowed_callers', [])
        if not isinstance(callers, list) or not callers or any(not isinstance(a, str) or not re.fullmatch(r'[a-z0-9-]+@[a-z0-9-]+\.iam\.gserviceaccount\.com', a) for a in callers):
            raise ValueError('Use explicit service account emails')
        for field in ['jar_prefixes', 'input_prefixes', 'output_prefixes', 'log_prefixes']:
            values = p.get(field, [])
            if not isinstance(values, list) or not values:
                raise ValueError(f'Missing {field}')
            for v in values:
                if not isinstance(v, str) or not v.endswith('/') or any(c in v for c in ['%', '\\', '*', '?', '#']) or any(ord(c) < 33 or ord(c) == 127 for c in v):
                    raise ValueError(f'Invalid {field}')
                uri = urlsplit(v)
                schemes = {'gs'} if field in {'jar_prefixes', 'log_prefixes'} else {'gs', 'hdfs'}
                if uri.scheme not in schemes or (uri.scheme == 'gs' and not re.fullmatch(r'[a-z0-9][a-z0-9._-]{1,220}[a-z0-9]', uri.netloc)) or any(x in {'.', '..'} for x in uri.path.split('/')):
                    raise ValueError(f'Invalid {field}')
    return profiles


def settings():
    return {
        'profiles': load_profiles(os.environ['CLUSTER_PROFILES']),
        'project': os.environ['GCP_PROJECT_ID'], 'region': os.environ['DATAPROC_REGION'],
        'database': os.environ['FIRESTORE_DATABASE'], 'topic': os.environ['JOB_TOPIC'],
        'prefix': os.environ['SERVICE_NAME'],
        'daily_limit': int(os.environ.get('DAILY_JOB_LIMIT', '100')),
        'rate_limit': int(os.environ.get('REQUESTS_PER_MINUTE', '60')),
        'retention': int(os.environ.get('RETENTION_DAYS', '30')),
    }

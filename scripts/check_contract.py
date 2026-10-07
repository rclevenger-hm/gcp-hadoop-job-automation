"""Check packaged entry points, examples, API and Terraform integration names."""
import ast
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.auth import Identity  # noqa: E402
from app.config import load_profiles  # noqa: E402
from app.validation import job_request  # noqa: E402


def main():
    profiles = load_profiles((ROOT / 'examples/profiles.json').read_text())
    payload = json.loads((ROOT / 'examples/job.json').read_text())
    caller = Identity('123', profiles['analytics']['allowed_callers'][0])
    assert job_request(payload, profiles, caller) == payload
    spec = yaml.safe_load((ROOT / 'openapi.yaml').read_text())
    assert set(spec['paths']) == {'/jobs', '/jobs/{job_id}', '/jobs/{job_id}/cancel', '/jobs/{job_id}/logs', '/usage'}
    names = {n.name for n in ast.parse((ROOT / 'main.py').read_text()).body if isinstance(n, ast.FunctionDef)}
    assert names == {'api', 'worker', 'reconcile'}
    infrastructure = '\n'.join(p.read_text() for p in (ROOT / 'terraform').glob('*.tf'))
    required = {'GCP_PROJECT_ID', 'DATAPROC_REGION', 'FIRESTORE_DATABASE', 'JOB_TOPIC', 'SERVICE_NAME', 'CLUSTER_PROFILES', 'TOKEN_AUDIENCE', 'ALLOWED_CALLER_EMAILS'}
    assert all(name in infrastructure for name in required)
    assert '"python313"' in infrastructure and 'dataproc.clusters.delete' not in infrastructure
    workflow = yaml.safe_load((ROOT / '.github/workflows/deploy.yml').read_text())
    assert workflow['permissions']['id-token'] == 'write'
    print('Examples, entry points, API routes, environment wiring, and private deployment contracts verified.')


if __name__ == '__main__':
    main()

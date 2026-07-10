"""Read-only deployment smoke test. Never submits a Hadoop job."""
import argparse

import requests

from client import token


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--impersonate', required=True)
    args = parser.parse_args()
    url = args.url.rstrip('/')
    anonymous = requests.get(url + '/usage', timeout=30, allow_redirects=False)
    assert anonymous.status_code in {401, 403}, f'Anonymous access returned {anonymous.status_code}'
    credential = token(url, args.impersonate)
    headers = {'Authorization': f'Bearer {credential}', 'X-Serverless-Authorization': f'Bearer {credential}'}
    result = requests.get(url + '/usage', headers=headers, timeout=30, allow_redirects=False)
    result.raise_for_status()
    data = result.json()
    assert isinstance(data['jobs'], int) and data['limit'] > 0
    print('Anonymous access denied; authorized quota read passed.')


if __name__ == '__main__':
    main()

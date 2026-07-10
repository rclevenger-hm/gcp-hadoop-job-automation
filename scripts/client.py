"""Service-account ID-token client; use ADC or explicit local impersonation."""
import argparse
import json
import sys
from urllib.parse import urlsplit

import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import requests


def token(audience, service_account=None):
    transport = Request()
    if service_account:
        source, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        target = impersonated_credentials.Credentials(source, service_account, target_scopes=['https://www.googleapis.com/auth/cloud-platform'], lifetime=600)
        credential = impersonated_credentials.IDTokenCredentials(target, target_audience=audience, include_email=True)
        credential.refresh(transport)
        return credential.token
    return id_token.fetch_id_token(transport, audience)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True, help='Canonical API function URL; also the token audience')
    parser.add_argument('--impersonate', help='Allowed caller service account for local ADC')
    commands = parser.add_subparsers(dest='command', required=True)
    submit = commands.add_parser('submit')
    submit.add_argument('--file', required=True)
    submit.add_argument('--key', required=True)
    for name in ['get', 'cancel', 'logs']:
        cmd = commands.add_parser(name)
        cmd.add_argument('job_id')
        if name == 'logs':
            cmd.add_argument('--segment', type=int, default=0)
            cmd.add_argument('--offset', type=int, default=0)
            cmd.add_argument('--limit', type=int, default=16384)
    history = commands.add_parser('history')
    history.add_argument('--limit', type=int, default=20)
    history.add_argument('--cursor')
    history.add_argument('--status')
    commands.add_parser('usage')
    args = parser.parse_args()
    url = args.url.rstrip('/')
    if urlsplit(url).scheme != 'https' or urlsplit(url).query or urlsplit(url).fragment:
        parser.error('--url must be an HTTPS endpoint without query or fragment')
    credential = token(url, args.impersonate)
    headers = {'Authorization': f'Bearer {credential}', 'X-Serverless-Authorization': f'Bearer {credential}'}
    method, path, payload, query = 'GET', '/jobs', None, {}
    if args.command == 'submit':
        method = 'POST'
        with open(args.file) as source:
            payload = json.load(source)
        headers['Idempotency-Key'] = args.key
    elif args.command == 'usage':
        path = '/usage'
    elif args.command == 'history':
        query = {k: getattr(args, k) for k in ['limit', 'cursor', 'status'] if getattr(args, k) is not None}
    else:
        path = f'/jobs/{args.job_id}'
        if args.command == 'cancel':
            method, path = 'POST', path + '/cancel'
        elif args.command == 'logs':
            path += '/logs'
            query = {k: getattr(args, k) for k in ['segment', 'offset', 'limit']}
    result = requests.request(method, url + path, json=payload, params=query, headers=headers, timeout=60, allow_redirects=False)
    print(result.text)
    return 0 if 200 <= result.status_code < 300 else 1


if __name__ == '__main__':
    sys.exit(main())

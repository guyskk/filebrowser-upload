# coding: utf-8
import argparse
import sys
from os.path import abspath, join, dirname, expanduser

VENDOR_PATH = abspath(join(dirname(__file__), 'vendor'))
sys.path.insert(0, VENDOR_PATH)

import requests
from .__version__ import __version__


def get_args():
    if '--version' in sys.argv:
        print(__version__)
        sys.exit(0)
    parser = argparse.ArgumentParser(description='Filebrowser upload.')
    parser.add_argument('filepath', help='local file path')
    parser.add_argument('--version', dest='version', help='Show version')
    parser.add_argument('--api', dest='api', required=True, help='Filebrowser upload API URL')
    parser.add_argument('--username', dest='username', required=True, help='Username')
    parser.add_argument('--password', dest='password', required=True, help='Password')
    parser.add_argument('--dest', dest='dest', required=True, help='File destination')
    parser.add_argument('--override', dest='override', action='store_true',
                        default=False, help='Override file or not')
    args = parser.parse_args()
    args.api = args.api.strip().rstrip('/')
    args.dest = args.dest.strip().lstrip('/')
    args.filepath = expanduser(args.filepath)
    return args


def get_login_url(CONFIG):
    return '{}/login'.format(CONFIG.api)


def get_upload_url(CONFIG):
    return '{}/resources/{}'.format(CONFIG.api, CONFIG.dest)


def get_token(CONFIG):
    response = requests.post(get_login_url(CONFIG), json={
        "password": CONFIG.password,
        "recaptcha": "",
        "username": CONFIG.username,
    })
    response.raise_for_status()
    return response.text


def upload(CONFIG):
    url = get_upload_url(CONFIG)
    print('Upload to {}'.format(url))
    token = get_token(CONFIG)
    override = 'true' if CONFIG.override else 'false'
    with open(CONFIG.filepath, 'rb') as data:
        response = requests.post(
            url, data=data,
            params={"override": override},
            headers={'X-Auth': token},
        )
    print('{} {}'.format(response.status_code, response.reason))


def main():
    upload(get_args())

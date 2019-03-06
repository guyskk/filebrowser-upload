# coding: utf-8
import argparse
import sys
import warnings
from os.path import abspath, join, dirname, expanduser

VENDOR_PATH = abspath(join(dirname(__file__), 'vendor'))
sys.path.insert(0, VENDOR_PATH)

import requests
from tqdm import tqdm
from urllib3.exceptions import InsecureRequestWarning
from .__version__ import __version__

warnings.simplefilter('ignore', InsecureRequestWarning)

try:
    from requests.utils import super_len
except ImportError:
    super_len = len


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
    parser.add_argument('--insecure', dest='insecure', action='store_true',
                        default=False, help='Allow insecure server connections when using SSL')
    parser.add_argument('--no-progress', dest='no_progress', action='store_true',
                        default=False, help='Disable progress bar')
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
    }, verify=not CONFIG.insecure)
    response.raise_for_status()
    return response.text


class ProgressFile:
    def __init__(self, fileobj):
        self.fileobj = fileobj
        self._length = super_len(self.fileobj)
        self.bar = tqdm(total=self._length, ncols=80, ascii=True, unit='B', unit_scale=True)

    def __len__(self):
        return self._length

    def read(self, size=-1):
        data = self.fileobj.read(size)
        self.bar.update(len(data))
        return data

    def close(self):
        self.bar.close()
        self.fileobj.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def upload(CONFIG):
    url = get_upload_url(CONFIG)
    print('Upload to {}'.format(url))
    try:
        token = get_token(CONFIG)
    except requests.exceptions.HTTPError as ex:
        print('Login failed: {} {}'.format(ex.response.status_code, ex.response.reason))
        return
    override = 'true' if CONFIG.override else 'false'
    fileobj = open(CONFIG.filepath, 'rb')
    if not CONFIG.no_progress:
        fileobj = ProgressFile(fileobj)
    with fileobj:
        response = requests.post(
            url, data=fileobj,
            params={"override": override},
            headers={'X-Auth': token},
            verify=not CONFIG.insecure,
        )
    print('{} {}'.format(response.status_code, response.reason))


def main():
    upload(get_args())

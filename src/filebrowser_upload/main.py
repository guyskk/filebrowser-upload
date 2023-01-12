# coding: utf-8

import posixpath
import argparse
import configparser
import sys
import warnings
from os import walk, getenv
from os.path import abspath, dirname, expanduser, join, isdir, isfile, basename, exists
from getpass import getpass

import requests
from tqdm import tqdm
from urllib3.exceptions import InsecureRequestWarning

from .__version__ import __version__

VENDOR_PATH = abspath(join(dirname(__file__), 'vendor'))
sys.path.insert(0, VENDOR_PATH)

warnings.simplefilter('ignore', InsecureRequestWarning)

try:
    from requests.utils import super_len
except ImportError:
    super_len = len


CONFIG_FILE_NAME = 'filebrowser_upload.ini'


def read_config(path: str) -> dict:
    '''
    Read the config file and return it as dictionary

    Args:
        path (str): path to config file

    Returns:
        dict: loaded configuration
    '''

    config = configparser.ConfigParser()
    config.read(path)

    return dict(config["filebrowser"])


def get_args():
    '''
    Get arguments.

    Returns:
        args, dict: Parsed arguments, loaded configuration.
    '''

    if '--version' in sys.argv:
        print(__version__)
        sys.exit(0)

    parser = argparse.ArgumentParser(description='Filebrowser upload.')

    parser.add_argument('src', type=str, help='Source file or folder')
    parser.add_argument(
        '--api',
        dest='api',
        default=argparse.SUPPRESS,
        help='Filebrowser upload API URL',
    )
    parser.add_argument(
        '--username', dest='username', default=argparse.SUPPRESS, help='Username'
    )
    parser.add_argument(
        '--dest',
        dest='dest',
        type=str,
        default='',
        help='Destination file or folder (Default is filebrowser home)',
    )
    parser.add_argument(
        '--password', dest='password', default=argparse.SUPPRESS, help='Inline password'
    )
    parser.add_argument(
        '--insecure',
        dest='insecure',
        action='store_true',
        default=False,
        help='Allow insecure server connections when using SSL',
    )
    parser.add_argument(
        '--no-progress',
        dest='no_progress',
        action='store_true',
        default=False,
        help='Disable progress bar',
    )
    parser.add_argument(
        '--override',
        dest='override',
        action='store_true',
        default=False,
        help='Override files or not',
    )
    parser.add_argument(
        '--dry-run',
        dest='dry_run',
        action='store_true',
        default=False,
        help='Dry run mode (no upload)',
    )

    parser.add_argument(
        '--only-folder-content',
        dest='only_folder_content',
        action='store_true',
        default=False,
        help='''Remove input folder from full path when uploading.
        Only content of input folder will be uploaded.''',
    )
    parser.add_argument('--version', dest='version', help='Show version')

    args = parser.parse_args()

    # Default param
    config = {
        'api': None,
        'username': None,
        'password': None,
    }

    config_paths = possible_config_paths()

    for path in config_paths:
        if exists(path):
            fileconfig = read_config(path)
            print(f'Configuration loaded from: {path}')
            config.update(fileconfig)
            break

    args_var = vars(args)

    # CLI takes precedence
    for key in config:
        if key in args_var:
            config[key] = args_var[key]

    # Validate mandatory params

    if config['api'] is None:
        raise TypeError("A Valid api param must be provided. Use -h for help.")

    if config['username'] is None:
        raise TypeError("A Valid username param must be provided. Use -h for help.")

    config['api'] = config['api'].strip().rstrip('/')
    check_url(config['api'])

    # Sanitize params

    args.src = expanduser(args.src.rstrip('/'))
    args.dest = args.dest.strip().lstrip('/')

    return args, config


def possible_config_paths():
    '''
    Paths were a config file should be found based on platform used

    Returns:
        list: A list of valid paths
    '''

    config_paths = [
        join(getenv('HOME') or '~', '.config', 'filebrowser_upload', CONFIG_FILE_NAME),
    ]

    if sys.platform == 'win32':
        config_paths.append(
            join(getenv('APPDATA'), 'filebrowser_upload', CONFIG_FILE_NAME)
        )
    elif sys.platform == 'darwin':
        config_paths.append(
            join(
                getenv('HOME') or '~',
                'Library',
                'Application Support',
                'filebrowser_upload',
                CONFIG_FILE_NAME,
            )
        )

    return config_paths


def check_url(url: str):
    '''
    Check if a url is valid. If it is not an exception will raise

    Args:
        url (str): url to check
    '''

    prepared_request = requests.models.PreparedRequest()
    prepared_request.prepare_url(url, None)


def get_login_url(config: dict):
    '''
    Compose the login url.

    Args:
        config (dict): loaded configuration

    Returns:
        str: Login url.
    '''
    return posixpath.join(config['api'], 'login')


def get_upload_url(args):
    '''
    Compose the upload url.

    Args:
        args (args): Parsed arguments.

    Returns:
        str: Upload url.
    '''
    return posixpath.join(args.api, 'resources', args.dest)


def get_token(args, config: dict):
    '''
    Get authentication token.

    Args:
        args (args): Parsed arguments.

    Returns:
        str: Authentication token.
    '''
    response = requests.post(
        get_login_url(config),
        json={
            'password': config['password'],
            'recaptcha': '',
            'username': config['username'],
        },
        verify=not args.insecure,
    )
    response.raise_for_status()
    return response.text


class ProgressFile:
    '''
    Progress file class for tqdm.
    '''

    def __init__(self, fileobj):
        self.fileobj = fileobj
        self._length = super_len(self.fileobj)
        self.pbar = tqdm(
            total=self._length, ncols=80, ascii=True, unit='B', unit_scale=True
        )

    def __len__(self):
        return self._length

    def read(self, size=-1):
        data = self.fileobj.read(size)
        self.pbar.update(len(data))
        return data

    def close(self):
        self.pbar.close()
        self.fileobj.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def upload(file, url, no_progress, override, headers, insecure, report):
    '''
    Upload file to the specified url.

    Args:
        file (str): File to be read.
        url (str): File destination url.
        no_progress (bool): Enable or disable progress bar.
        override (bool): Override file or not.
        headers (dict): Authentication headers.
        insecure (bool): Allow insecure server connections when using SSL.
        report (dict): Update upload report.
    '''

    fileobj = open(file, 'rb')

    if not no_progress:
        fileobj = ProgressFile(fileobj)

    with fileobj:
        response = requests.post(
            url,
            data=fileobj,
            params={'override': override},
            headers=headers,
            verify=not insecure,
        )

    report_key = f'{response.status_code} {response.reason}'
    print(f'{report_key}\n')

    if report.get(report_key):
        report[report_key] += 1
    else:
        report[report_key] = 1


def traverse_fs_and_upload(args, url, override, headers, report):
    '''
    Traverse the folder in top-down way starting from a given path and upload all files

    Args:
        args: Parsed arguments
        url (str): Upload url
        override (bool): Override files or not
        headers (dict): Authentication headers
        report (dict): Update upload report
    '''

    # e.g.: args.src is /home/user/test/upload_folder
    # This means that I want to upload the directory named 'upload_folder'
    # Rest of the path must not be part of the destination url
    # fixed_prefix for this example will be /home/user/test
    # Same logic applies for relative path (e.g. test/upload_folder)
    fixed_prefix = dirname(args.src)

    for path, _, files in walk(args.src):
        for file in files:
            if args.only_folder_content:
                path_no_prefix = path.removeprefix(args.src)
            else:
                path_no_prefix = path.replace(fixed_prefix, '')

            file_full_url = posixpath.join(
                url, path_no_prefix.lstrip('/'), file.lstrip('/')
            )

            file = join(path, file)

            print(f'Uploading {file} to {file_full_url}')

            if not args.dry_run:
                upload(
                    file,
                    file_full_url,
                    args.no_progress,
                    override,
                    headers,
                    args.insecure,
                    report,
                )


def main():
    '''
    Main function. Get arguments, login, upload files.
    '''
    print('Welcome to filebrowser-upload')
    args, config = get_args()

    if config['password'] is None:
        config['password'] = getpass('Password: ')

    try:
        token = get_token(args, config)
    except requests.exceptions.HTTPError as ex:
        status_code = ex.response.status_code
        reason = ex.response.reason

        sys.exit(f'Login failed for user {config["username"]}: {status_code} {reason}')

    override = 'true' if args.override else 'false'

    headers = {
        'X-Auth': token,  # version >= 2.0.3 seems use this header
        'Authorization': f'Bearer {token}',  # version <= 2.0.0 seems use this header
    }

    report = {}

    if isdir(args.src):
        print('Folder upload detected...\n')
        url = get_upload_url(args)
        traverse_fs_and_upload(args, url, override, headers, report)
    elif isfile(args.src):
        print('File upload detected...\n')

        # if dest is not defined, use input file name as dest
        if args.dest == '':
            args.dest = basename(args.src)

        url = get_upload_url(args)

        print(f'Uploading {args.src} to {url}')
        if not args.dry_run:
            upload(
                args.src,
                url,
                args.no_progress,
                override,
                headers,
                args.insecure,
                report,
            )

    if not args.dry_run:
        print('\nUpload completed with the following report:')

        for key, value in report.items():
            print(f'\t{value} item were uploaded with code {key}')
    else:
        print('\nThis was a dry-run session. Nothing changed.')

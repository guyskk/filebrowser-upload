# coding: utf-8

import posixpath
import argparse
import sys
import warnings
from os import walk
from os.path import abspath, dirname, expanduser, join
from getpass import getpass

import requests
from tqdm import tqdm
from urllib3.exceptions import InsecureRequestWarning

from .__version__ import __version__

VENDOR_PATH = abspath(join(dirname(__file__), "vendor"))
sys.path.insert(0, VENDOR_PATH)

warnings.simplefilter("ignore", InsecureRequestWarning)

try:
    from requests.utils import super_len
except ImportError:
    super_len = len


def get_args():
    """
    Get arguments.

    Returns:
        args: Parsed arguments.
    """
    if "--version" in sys.argv:
        print(__version__)
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Filebrowser upload.")
    parser.add_argument("--version", dest="version", help="Show version")
    parser.add_argument(
        "--api", dest="api", required=True, help="Filebrowser upload API URL"
    )
    parser.add_argument("--username", dest="username", required=True, help="Username")
    parser.add_argument("--password", dest="password", help="Inline password")
    parser.add_argument(
        "--insecure",
        dest="insecure",
        action="store_true",
        default=False,
        help="Allow insecure server connections when using SSL",
    )
    parser.add_argument(
        "--no-progress",
        dest="no_progress",
        action="store_true",
        default=False,
        help="Disable progress bar",
    )
    parser.add_argument(
        "--override",
        dest="override",
        action="store_true",
        default=False,
        help="Override files or not",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Dry run mode (no upload)",
    )
    parser.add_argument(
        "--no-input-folder",
        dest="no_input_folder",
        action="store_true",
        default=False,
        help="""Remove input folder from full path when uploading.
        Only content of input folder will be uploaded.""",
    )

    subparsers = parser.add_subparsers(
        help="Commands for single file upload or entire folder", dest="subcommand"
    )

    # Parser for file command
    file_parser = subparsers.add_parser("file", help="Single file upload")
    file_parser.add_argument("src", type=str, help="Source file")
    file_parser.add_argument("dest", type=str, help="Destination file")

    # Parser for folder command
    folder_parser = subparsers.add_parser(
        "folder", help="Entire folder and subfolders upload"
    )
    folder_parser.add_argument("src", type=str, help="Source folder")
    folder_parser.add_argument("dest", type=str, help="Destination folder")

    args = parser.parse_args()
    args.api = args.api.strip().rstrip("/")
    args.src = expanduser(args.src)
    args.dest = args.dest.strip().lstrip("/")

    return args


def get_login_url(config):
    """
    Compose the login url.

    Args:
        config (args): Parsed arguments.

    Returns:
        str: Login url.
    """
    return posixpath.join(config.api, "login")


def get_upload_url(config):
    """
    Compose the upload url.

    Args:
        config (args): Parsed arguments.

    Returns:
        str: Upload url.
    """
    return posixpath.join(config.api, "resources", config.dest)


def get_token(config):
    """
    Get authentication token.

    Args:
        config (args): Parsed arguments.

    Returns:
        str: Authentication token.
    """
    response = requests.post(
        get_login_url(config),
        json={
            "password": config.password,
            "recaptcha": "",
            "username": config.username,
        },
        verify=not config.insecure,
    )
    response.raise_for_status()
    return response.text


class ProgressFile:
    """
    Progress file class for tqdm.
    """

    def __init__(self, fileobj):
        self.fileobj = fileobj
        self._length = super_len(self.fileobj)
        self.pbar = tqdm(
            total=self._length, ncols=80, ascii=True, unit="B", unit_scale=True
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


def upload(file, url, no_progress, override, headers, insecure):
    """
    Upload file to the specified url.

    Args:
        file (str): File to be read.
        url (str): File destination url.
        no_progress (bool): Enable or disable progress bar.
        override (bool): Override file or not.
        headers (dict): Authentication headers.
        insecure (bool): Allow insecure server connections when using SSL.
    """
    fileobj = open(file, "rb")

    if not no_progress:
        fileobj = ProgressFile(fileobj)

    with fileobj:
        response = requests.post(
            url,
            data=fileobj,
            params={"override": override},
            headers=headers,
            verify=not insecure,
        )

    print(f"{response.status_code} {response.reason}")


def main():
    """
    Main function. Get arguments, login, upload files.
    """
    args = get_args()

    if args.password is None:
        args.password = getpass("Password: ")

    try:
        token = get_token(args)
    except requests.exceptions.HTTPError as ex:
        print(f"Login failed: {ex.response.status_code} {ex.response.reason}")
        return

    override = "true" if args.override else "false"

    headers = {
        "X-Auth": token,  # version >= 2.0.3 seems use this header
        "Authorization": f"Bearer {token}",  # version <= 2.0.0 seems use this header
    }

    url = get_upload_url(args)

    if args.subcommand == "folder":
        # Traverse the folder in top-down way and upload all files
        for path, _, files in walk(args.src):
            for file in files:
                if args.no_input_folder:
                    path = path.removeprefix(args.src)

                file = join(path, file).lstrip("/")
                file_full_url = posixpath.join(url, file)

                print(f"Uploading to {file_full_url}")

                if not args.dry_run:
                    upload(
                        file,
                        file_full_url,
                        args.no_progress,
                        override,
                        headers,
                        args.insecure,
                    )
    elif args.subcommand == "file":
        print(f"Uploading to {url}")
        if not args.dry_run:
            upload(args.src, url, args.no_progress, override, headers, args.insecure)

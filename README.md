# filebrowser-upload

Upload command for <https://github.com/filebrowser/filebrowser>

## Install

Download binary executable from <https://github.com/guyskk/filebrowser-upload/releases> or build with

```console
foo@bar:~$ ./release.sh
```

In ```dist``` folder you will find the executable.

## Usage

```console
usage: filebrowser-upload [-h] [--api API] [--username USERNAME] [--password PASSWORD] [--dest DEST]
                          [--insecure] [--no-progress] [--override]
                          [--dry-run] [--only-folder-content] [--version VERSION]
                          src

Filebrowser upload.

positional arguments:
  src                   Source file or folder

optional arguments:
  -h, --help             show this help message and exit
  --api API              Filebrowser upload API URL
  --username USERNAME    Login username
  --password PASSWORD    Login password (use inline in safe environment)
  --dest DEST            Destination file or folder (Default is filebrowser home)
  --insecure             Allow insecure server connections when using SSL
  --no-progress          Disable progress bar
  --override             Override files or not
  --dry-run              Dry run mode (no upload)
  --only-folder-content  Remove input folder from full path when uploading. Only content of input folder will be uploaded.
  --version VERSION      Show version
```

> :warning: **Specify password via params only in safe environment**

## Examples

### Single file upload

```console
filebrowser-upload \
    --api http://127.0.0.1:8000/api/ \
    --username admin \
    foo.bar
```

Uploads to: ```http://127.0.0.1:8000/api/resources/foo.bar```

```console
filebrowser-upload \
    --api http://127.0.0.1:8000/api/ \
    --username admin \
    --dest a_folder/new_foo.bar
    foo.bar
```

Uploads to: ```http://127.0.0.1:8000/api/resources/a_folder/new_foo.bar```

### Folder upload

```console
filebrowser-upload \
    --api http://127.0.0.1:8000/api/ \
    --username admin \
    foo
```

Uploads to: ```http://127.0.0.1:8000/api/resources/foo/<folder_content>```

```console
filebrowser-upload \
    --api http://127.0.0.1:8000/api/ \
    --username admin \
    --dest bar
    foo
```

Uploads to: ```http://127.0.0.1:8000/api/resources/bar/foo/<folder_content>```

With ```--only-folder-content```

```console
filebrowser-upload \
    --api http://127.0.0.1:8000/api/ \
    --username admin \
    --dest bar
    --only-folder-content
    foo
```

Uploads to: ```http://127.0.0.1:8000/api/resources/bar/<folder_content>```

### Dry run

Just add the ```--dry-run``` param. Files will not be uploaded.

### Testing

Create a folder ```test_upload``` in the repository root and add files/folder there.

## Configuration

You can also create a config file to store fixed params and avoid to input them everytime.

Configuration file is expected to be found in:

- `~/.config/filebrowser_upload/filebrowser_upload.ini`
- `%APPDATA%/filebrowser_upload/filebrowser_upload.ini` (Windows)
- `~/Library/Application Support/filebrowser_upload/filebrowser_upload.ini` (MacOS)

(Credit for starting idea goes to: <https://github.com/r4sas/PBinCLI>)

### Example of config file content

```ini
[filebrowser]
api = https://myfilebrowser.instance/api
```

### List of param available

| Option   | Default | Description                |
|----------|---------|----------------------------|
| api      | None    | Filebrowser upload API URL |
| username | None    | Login username             |
| password | None    | Login password             |

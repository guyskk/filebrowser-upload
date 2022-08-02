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
usage: filebrowser-upload [-h] [--version VERSION] --api API --username USERNAME 
                          [--password PASSWORD] [--insecure] [--no-progress] 
                          [--override] [--dry-run]
                          {file,folder} ...

Filebrowser upload.

positional arguments:
  {file,folder}        Commands for single file upload or entire folder
    file               Single file upload
    folder             Entire folder and subfolders upload

optional arguments:
  -h, --help           show this help message and exit
  --version VERSION    Show version
  --api API            Filebrowser upload API URL
  --username USERNAME  Username
  --password PASSWORD  Inline password
  --insecure           Allow insecure server connections when using SSL
  --no-progress        Disable progress bar
  --override           Override files or not
  --dry-run            Dry run mode (no upload)
  --no-input-folder    Remove input folder from full path when uploading. Only content of input folder will be uploaded.
```

> :warning: **Specify password via params only in safe environment**

## Example

### Single file upload

```console
filebrowser-upload \
    --api http://127.0.0.1:8000/api/ \
    --username admin \
    file README.md README.md
```

### Folder upload

```console
filebrowser-upload \
    --api http://127.0.0.1:8000/api/ \
    --username admin \
    folder foo bar
```

### Dry run

Just add the ```--dry-run``` param. Files will not be uploaded.

## Testing

Create a folder ```test_upload``` in the repository root and add files/folder there.

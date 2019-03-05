# filebrowser-upload

Upload command for https://github.com/filebrowser/filebrowser

## Install

Download binary executable from https://github.com/guyskk/filebrowser-upload/releases

## Usage

```
Filebrowser upload.

positional arguments:
  filepath             local file path

optional arguments:
  -h, --help           show this help message and exit
  --version VERSION    Show version
  --api API            Filebrowser upload API URL
  --username USERNAME  Username
  --password PASSWORD  Password
  --dest DEST          File destination
  --override           Override file or not
```

## Example

```
filebrowser-upload \
    --api http://127.0.0.1:8000/api \
    --username admin \
    --password admin \
    --override \
    --dest README.md \
    README.md
```

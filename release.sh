#!/bin/bash

set -ex
mkdir -p src/filebrowser_upload/vendor
python setup.py vendor
python setup.py sdist
python setup.py package
chmod u+x dist/filebrowser-upload
ls -lh dist
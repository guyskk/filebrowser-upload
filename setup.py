# coding: utf-8
import re
import fnmatch
import shutil
import os.path
from setuptools import Command, setup


VENDOR_PATH = 'src/filebrowser_upload/vendor'


def get_version():
    with open('src/filebrowser_upload/__version__.py', 'rb') as f:
        content = f.read().decode('utf-8')
        quotes = '[{}{}]'.format('"', "'")
        pattern = r'__version__ = {q}([\d\.]+?){q}'.format(q=quotes)
        return re.search(pattern, content).group(1)


__version__ = get_version()


def _clean(patterns):
    base = os.getcwd().rstrip('/')
    for root, dirnames, filenames in os.walk(base):
        for name in dirnames + filenames:
            fullpath = os.path.join(root, name)
            fullname = fullpath[len(base) + 1:]
            for pattern in patterns:
                if fnmatch.fnmatch(fullname, pattern):
                    print(fullname)
                    if os.path.isdir(fullpath):
                        shutil.rmtree(fullpath)
                    elif os.path.exists(fullpath):
                        os.remove(fullpath)


class VendorCommand(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        shutil.rmtree(VENDOR_PATH)
        os.system('pip install --no-binary :all --no-compile --no-deps -r requirements.txt -t {}'
                  .format(VENDOR_PATH))
        _clean([
            '**/vendor/bin',
            '**/vendor/*.dist-info',
            '**/vendor/*.so',
            '**/*.egg-info',
            '**/__pycache__',
            '**/*.py[co]',
        ])


class PackageCommand(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        _clean([
            '**/*.egg-info',
            '**/__pycache__',
            '**/*.py[co]',
        ])
        if not os.path.exists('dist'):
            os.makedirs('dist')
        os.system("cd src && zip -r - * > ../dist/filebrowser-upload")
        with open('dist/filebrowser-upload', 'rb+') as f:
            data = f.read()
            f.seek(0)
            f.write(b'#!/usr/bin/env python\n')
            f.write(data)
        os.system('chmod u+x dist/filebrowser-upload')


setup(
    cmdclass={
        'vendor': VendorCommand,
        'package': PackageCommand,
    },
    name='filebrowser-upload',
    version=__version__,
    description='Watch PATH and rsync to DEST',
    author='guyskk',
    author_email='guyskk@qq.com',
    url='https://github.com/guyskk/filebrowser-upload',
    packages=['filebrowser_upload'],
    package_dir={'': 'src'},
    include_package_data=True,
    entry_points={
        'console_scripts': ['filebrowser-upload=filebrowser_upload.main:main']
    },
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
)
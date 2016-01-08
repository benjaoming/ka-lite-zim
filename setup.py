#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
doclink = """
Documentation
-------------

The full documentation is at http://ka-lite-zim.rtfd.org."""
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='ka-lite-zim',
    version='0.1.0',
    description='OpenZIM export command for ka-lite',
    long_description=readme + '\n\n' + doclink + '\n\n' + history,
    author='Benjamin Bach',
    author_email='benjamin@learningequality.org',
    url='https://github.com/benjaoming/ka-lite-zim',
    packages=[
        'kalite_zim',
    ],
    package_dir={'ka-lite-zim': 'kalite_zim'},
    include_package_data=True,
    install_requires=[
        'ka-lite>=0.15,<0.16',
        'colorlog',
        'django-compressor==1.6',
        'django-libsass==0.6',
        'libsass==0.10.0',
    ],
    license='MIT',
    zip_safe=False,
    keywords='ka-lite-zim',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)

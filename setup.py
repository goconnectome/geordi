#!/usr/bin/env python
"""Installs alastor"""

import os
import sys
from distutils.core import setup

def long_description():
    """Get the long description from the README"""
    return open(os.path.join(sys.path[0], 'README.txt')).read()

setup(
    author='Brodie Rao',
    author_email='brodie@sf.io',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: JavaScript',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    description='A Django middleware for interactive profiling',
    download_url='', # XXX
    keywords='django graph profiler',
    license='GNU GPL',
    long_description=long_description(),
    name='alastor',
    packages=['alastor'],
    url='http://bitheap.org/alastor/',
    version='0.1',
)

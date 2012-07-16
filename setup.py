#!/usr/bin/env python
"""Installs geordi"""

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
        ('License :: OSI Approved :: '
         'GNU Lesser General Public License v2 (LGPLv2)'),
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: JavaScript',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    description='A Django middleware for interactive profiling',
    dependency_links=[
        'https://bitbucket.org/brodie/gprof2dot/get/3d61cf0a321e06edc252d45e135ffea2bd16c1cc.tar.gz#egg=gprof2dot-dev'
    ],
    download_url='https://bitbucket.org/brodie/geordi/get/0.2.tar.gz',
    install_requires=['gprof2dot==dev'],
    keywords='django graph profiler',
    license='GNU Lesser GPL',
    long_description=long_description(),
    name='geordi',
    packages=['geordi'],
    url='https://bitbucket.org/brodie/geordi',
    version='0.2',
)

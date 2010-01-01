#!/usr/bin/env python
#
# This file is part of Jamaendo.
# Copyright (c) 2010, Kristoffer Gronlund
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Jamaendo nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from setuptools import setup, find_packages
from glob import glob
import os
import sys

running_on_tablet = os.path.exists('/etc/osso_software_version')

applications_dir = 'share/applications'
if running_on_tablet:
    applications_dir += '/hildon'

data_files = [
    ('share/jamaendo', glob('data/*.png')),
    (applications_dir, ['data/jamaendo.desktop']),
    ('share/icons/hicolor/scalable/apps', ['data/jamaendo.png']),
]

import sys
setup(
    name = "jamaendo",
    version = "0.0.1",
    author = "Kristoffer Gronlund",
    author_email = "kristoffer.gronlund@purplescout.se",
    url = "http://github.com/krig/jamaendo",
    packages = find_packages(exclude=['tests']),
    zip_safe=False,
    test_suite='tests.test_suite',
    scripts = ['scripts/jamaendo'],
    data_files = data_files
    )


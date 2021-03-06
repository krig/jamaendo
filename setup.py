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

from distutils.core import setup
from glob import glob

def get_version():
    from subprocess import Popen, PIPE
    p1 = Popen("grep -m 1 VERSION jamaui/ui.py".split(), stdout=PIPE)
    p2 = Popen("cut -d ' -f 2".split(), stdin=p1.stdout, stdout=PIPE)
    return p2.communicate()[0].strip()

data_files = [
    ('/opt/jamaendo', glob('data/icon_*.png') + ['data/bg.png', 'data/album.png']),
    ('share/applications/hildon', ['data/jamaendo.desktop']),
    ('share/icons/hicolor/26x26/apps', ['data/26x26/jamaendo.png']),
    ('share/icons/hicolor/40x40/apps', ['data/40x40/jamaendo.png']),
    ('share/icons/hicolor/scalable/apps', ['data/64x64/jamaendo.png']),
]

# search for translations and repare to install
#translation_files = []
#for mofile in glob('data/locale/*/LC_MESSAGES/jamaendo.mo'):
#    modir = os.path.dirname(mofile).replace('data', 'share')
#    translation_files.append((modir, [mofile]))

setup(
    name = "jamaendo",
    version = get_version(),
    author = "Kristoffer Gronlund",
    author_email = "kristoffer.gronlund@purplescout.se",
    url = "http://jamaendo.garage.maemo.org/",
    packages = ['jamaendo', 'jamaui'],
    scripts = ['scripts/jamaendo'],
    data_files = data_files# + translation_files,
    )


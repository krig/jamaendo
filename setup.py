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


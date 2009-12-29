from setuptools import setup, find_packages

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
    )


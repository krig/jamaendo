#!/usr/bin/env python
#
# This file is part of Jamaendo.
# Copyright (c) 2010 Kristoffer Gronlund
#
# Jamaendo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jamaendo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jamaendo.  If not, see <http://www.gnu.org/licenses/>.
#
# Player code heavily based on http://thpinfo.com/2008/panucci/:
#  A resuming media player for Podcasts and Audiobooks
#  Copyright (c) 2008-05-26 Thomas Perl <thpinfo.com>
#  (based on http://pygstdocs.berlios.de/pygst-tutorial/seeking.html)
#

import logging
import sys

LOG_FILENAME = '/tmp/jamaendo.log'
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s %(name)-10s: [%(lineno)4d] %(levelname)-5s %(message)s"

_rootlogger = logging.getLogger()
_fhandler = logging.FileHandler(LOG_FILENAME)
_shandler = logging.StreamHandler()
_formatter = logging.Formatter(LOG_FORMAT)
_fhandler.setFormatter(_formatter)
_shandler.setFormatter(_formatter)

_rootlogger.addHandler(_fhandler)
_rootlogger.addHandler(_shandler)
_rootlogger.setLevel(LOG_LEVEL)


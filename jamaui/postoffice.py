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
# message central

import logging

log = logging.getLogger(__name__)

class PostOffice(object):

    def __init__(self):
        self.tags = {} # tag -> [callback]

    def notify(self, tag, *data):
        clients = self.tags.get(tag)
        if clients:
            for ref, client in clients:
                client(*data)

    def connect(self, tag, ref, callback):
        if not isinstance(tag, list):
            tag = [tag]
        for t in tag:
            if t not in self.tags:
                self.tags[t] = []
            clients = self.tags[t]
            if callback not in clients:
                clients.append((ref, callback))

    def disconnect(self, tag, ref):
        if not isinstance(tag, list):
            tag = [tag]
        for t in tag:
            if t not in self.tags:
                self.tags[t] = []
            self.tags[t] = [(_ref, cb) for _ref, cb in self.tags[t] if _ref != ref]

postoffice = PostOffice()



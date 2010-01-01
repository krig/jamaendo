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

class PostOffice(object):
    class Client(object):
        def __init__(self):
            self.tags = {}
        def has_tag(self, tag):
            return tag in self.tags
        def notify(self, tags, data):
            for tag in tags:
                cb = self.tags.get(tag)
                if cb:
                    cb(data)
        def register(self, tag, callback):
            self.tags[tag] = callback

    def __init__(self):
        self.clients = {}

    def notify(self, tags, data):
        if not isinstance(tags, list):
            tags = [tags]
        for client in clients:
            client.notify(tags, data)

    def register(self, client_id, tag, callback):
        client = self.clients.get(client_id)
        if not client:
            client = Client()
            self.clients[client_id] = client
        client.register(tag, callback)

postoffice = PostOffice()



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
import gtk
try:
    import hildon
except:
    import helldon as hildon
import jamaendo
from playerwindow import open_playerwindow
from albumlist import RadioList
from fetcher import Fetcher

class RadiosWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.fetcher = None
        self.radios = {}

        self.set_title("Radios")
        self.connect('destroy', self.on_destroy)

        # Results list
        self.panarea = hildon.PannableArea()
        self.radiolist = RadioList()
        self.radiolist.connect('row-activated', self.row_activated)
        self.panarea.add(self.radiolist)
        self.add(self.panarea)

        self.start_radio_fetcher()

    def on_destroy(self, wnd):
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None

    def row_activated(self, treeview, path, view_column):
        name, _id = self.radiolist.get_radio_id(path)
        wnd = open_playerwindow()
        wnd.play_radio(name, _id)

    def start_radio_fetcher(self):
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None
        self.fetcher = Fetcher(jamaendo.starred_radios, self,
                               on_item = self.on_radio_result,
                               on_ok = self.on_radio_complete,
                               on_fail = self.on_radio_complete)
        self.fetcher.start()

    def on_radio_result(self, wnd, item):
        if wnd is self:
            self.radios[item.ID] = item
            self.radiolist.add_radios([item])

    def on_radio_complete(self, wnd, error=None):
        if wnd is self:
            self.fetcher.stop()
            self.fetcher = None

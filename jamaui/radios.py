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
import hildon
import jamaendo
from playerwindow import open_playerwindow
from albumlist import RadioList

class RadiosWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Radios")

        # Results list
        self.panarea = hildon.PannableArea()
        self.radiolist = RadioList()
        self.radiolist.connect('row-activated', self.row_activated)

        self.panarea.add(self.radiolist)

        self.radios = {}
        hildon.hildon_gtk_window_set_progress_indicator(self, 1)
        radios = jamaendo.starred_radios()
        for item in radios:
            self.radios[item.ID] = item
        self.radiolist.add_radios(radios)
        hildon.hildon_gtk_window_set_progress_indicator(self, 0)

        self.add(self.panarea)

    def make_button(self, text, subtext, callback):
        button = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                               hildon.BUTTON_ARRANGEMENT_VERTICAL)
        button.set_text(text, subtext)

        if callback:
            button.connect('clicked', callback)

        return button

    def row_activated(self, treeview, path, view_column):
        name, _id = self.radiolist.get_radio_id(path)
        wnd = open_playerwindow()
        wnd.play_radio(name, _id)

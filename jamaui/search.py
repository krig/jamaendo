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
from showartist import ShowArtist
from showalbum import ShowAlbum

class SearchWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Search")

        vbox = gtk.VBox(False, 0)


        # Results list
        self.panarea = hildon.PannableArea()
        self.result_store = gtk.ListStore(str, int)
        #self.result_store.append(['red'])
        self.result_view = gtk.TreeView(self.result_store)
        col = gtk.TreeViewColumn('Name')
        self.result_view.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', 0)
        self.result_view.set_search_column(0)
        col.set_sort_column_id(0)
        self.result_view.connect('row-activated', self.row_activated)

        self.panarea.add(self.result_view)
        vbox.pack_start(self.panarea, True, True, 0)


        # Create selector for search mode
        self.mode_selector = hildon.TouchSelector(text=True)

        self.mode_selector.append_text("Artists")
        self.mode_selector.append_text("Albums")
        self.mode_selector.append_text("Tracks")
        self.mode = hildon.PickerButton(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                        hildon.BUTTON_ARRANGEMENT_VERTICAL)
        self.mode.set_title("Search for")
        self.mode.set_selector(self.mode_selector)
        self.mode_selector.connect("changed", self.mode_changed)
        #vbox.pack_start(self.mode, False)
        self.mode.set_active(1)


        # Search box
        hbox = gtk.HBox(False, 0)
        self.entry = hildon.Entry(gtk.HILDON_SIZE_FINGER_HEIGHT)
        self.entry.set_placeholder("Search")
        self.entry.connect('activate', self.on_search)
        btn = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        btn.set_label(">>")
        btn.connect('clicked', self.on_search)
        hbox.pack_start(self.mode, False)
        hbox.pack_start(self.entry, True, True, 0)
        hbox.pack_start(btn, False)
        vbox.pack_start(hbox, False)


        self.add(vbox)

        self.idmap = {}

    def mode_changed(self, selector, user_data):
        current_selection = selector.get_current_text()
        print current_selection

    def on_search(self, w):
        mode = self.mode.get_active()
        txt = self.entry.get_text()
        self.result_store.clear()
        if mode == 0:
            for artist in jamaendo.search_artists(query=txt):
                title = artist.name
                self.idmap[artist.ID] = artist
                self.result_store.append([title, artist.ID])
        elif mode == 1:
            for album in jamaendo.search_albums(query=txt):
                title = "%s - %s" % (album.artist_name, album.name)
                self.idmap[album.ID] = album
                self.result_store.append([title, album.ID])
        elif mode == 2:
            for track in jamaendo.search_tracks(query=txt):
                title = "%s - %s" % (track.artist_name, track.name)
                self.idmap[track.ID] = track
                self.result_store.append([title, track.ID])

    def row_activated(self, treeview, path, view_column):
        treeiter = self.result_store.get_iter(path)
        title, _id = self.result_store.get(treeiter, 0, 1)
        item = self.idmap[_id]
        print _id, item
        self.open_item(item)

    def open_item(self, item):
        if isinstance(item, jamaendo.Album):
            wnd = ShowAlbum(item)
            wnd.show_all()
        elif isinstance(item, jamaendo.Artist):
            wnd = ShowArtist(item)
            wnd.show_all()
        elif isinstance(item, jamaendo.Track):
            wnd = open_playerwindow()
            wnd.play_tracks([item])

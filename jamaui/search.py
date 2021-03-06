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
from showartist import ShowArtist
from showalbum import ShowAlbum
from albumlist import MusicList
from fetcher import Fetcher

class SearchWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Search")
        self.idmap = {}

        vbox = gtk.VBox(False, 0)

        self.fetcher = None
        self.connect('destroy', self.on_destroy)

        # Results list
        self.panarea = hildon.PannableArea()
        self.musiclist = MusicList()
        self.musiclist.loading_message = "Nothing found yet"
        self.musiclist.empty_message = "No matching results"
        self.musiclist.connect('row-activated', self.row_activated)
        self.panarea.add(self.musiclist)
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

        self.create_menu()

    def create_menu(self):
        def on_player(*args):
            from playerwindow import open_playerwindow
            open_playerwindow()
        self.menu = hildon.AppMenu()
        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Open player")
        player.connect("clicked", on_player)
        self.menu.append(player)
        self.menu.show_all()
        self.set_app_menu(self.menu)

    def on_destroy(self, wnd):
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None

    def mode_changed(self, selector, user_data):
        pass
        #current_selection = selector.get_current_text()

    def on_search(self, w):
        mode = self.mode.get_active()
        txt = self.entry.get_text()
        self.musiclist.set_loading(False)
        self.musiclist.empty_message = "Searching..."
        self.musiclist.get_model().clear()

        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None

        itemgen = None
        if mode == 0:
            itemgen = lambda: jamaendo.search_artists(query=txt)
        elif mode == 1:
            itemgen = lambda: jamaendo.search_albums(query=txt)
        elif mode == 2:
            itemgen = lambda: jamaendo.search_tracks(query=txt)
        else:
            return

        self.fetcher = Fetcher(itemgen, self,
                               on_item = self.on_add_result,
                               on_ok = self.on_add_complete,
                               on_fail = self.on_add_complete)
        self.fetcher.start()
        '''
        try:
            if mode == 0:
                items = jamaendo.search_artists(query=txt)
            elif mode == 1:
                items = jamaendo.search_albums(query=txt)
            elif mode == 2:
                items = jamaendo.search_tracks(query=txt)

            for item in items:
                self.idmap[item.ID] = item

            self.musiclist.add_items(items)
        except jamaendo.JamaendoAPIException:
            # nothing found, force redraw
            self.musiclist.queue_draw()
        '''

    def on_add_result(self, wnd, item):
        if wnd is self:
            self.musiclist.add_items([item])
            self.idmap[item.ID] = item

    def on_add_complete(self, wnd, error=None):
        if wnd is self:
            self.musiclist.empty_message = "No matching results"
            self.musiclist.queue_draw()
            self.fetcher.stop()
            self.fetcher = None

    def row_activated(self, treeview, path, view_column):
        _id = self.musiclist.get_item_id(path)
        item = self.idmap[_id]
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

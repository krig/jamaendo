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
from albumlist import MusicList
from player import Playlist

def _alist(l, match):
    for key, value in l:
        if key == match:
            return value
    return None

class FeaturedWindow(hildon.StackableWindow):
    features = (("Albums of the week",jamaendo.albums_of_the_week),
                ("Tracks of the week",jamaendo.tracks_of_the_week),
                ("New releases",jamaendo.new_releases),
                ("Top 50 tags", lambda: jamaendo.top_tags(count=50)),
                ("Top 50 albums", lambda: jamaendo.top_albums(count=50)),
                ("Top 50 tracks", lambda: jamaendo.top_tracks(count=50)),
                )

    def __init__(self, feature):
        hildon.StackableWindow.__init__(self)
        self.set_title(feature)

        self.featurefn = _alist(self.features, feature)

        # Results list
        self.panarea = hildon.PannableArea()
        self.musiclist = MusicList()
        self.musiclist.connect('row-activated', self.row_activated)
        self.panarea.add(self.musiclist)

        self.idmap = {}
        self.items = self.featurefn()
        for item in self.items:
            self.idmap[item.ID] = item
        self.musiclist.add_items(self.items)

        self.add(self.panarea)

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
            playlist = Playlist(self.items)
            playlist.jump_to(item.ID)
            wnd = open_playerwindow()
            wnd.play_tracks(playlist)
        elif isinstance(item, jamaendo.Tag):
            wnd = open_playerwindow()
            wnd.play_tracks(jamaendo.get_tag_tracks(item.ID))

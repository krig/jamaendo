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
from player import Playlist
from fetcher import Fetcher
import logging

log = logging.getLogger(__name__)

def _alist(l, match):
    for key, value in l:
        if key == match:
            return value
    return None

class FeaturedWindow(hildon.StackableWindow):
    features = (
        ("New releases",jamaendo.new_releases),
        ("Top albums today", lambda: jamaendo.top_albums(order='ratingday_desc')),
        ("Top tracks today", lambda: jamaendo.top_tracks(order='ratingday_desc')),
        ("Albums of the week",jamaendo.albums_of_the_week),
        ("Tracks of the week",jamaendo.tracks_of_the_week),
        ("Top 50 tags", lambda: jamaendo.top_tags(count=50)),
        ("Top 50 artists", lambda: jamaendo.top_artists(count=50)),
        ("Top 50 albums", lambda: jamaendo.top_albums(count=50)),
        ("Top 50 tracks", lambda: jamaendo.top_tracks(count=50)),
        )

    def __init__(self, feature):
        hildon.StackableWindow.__init__(self)
        self.set_title(feature)

        self.fetcher = None
        self.connect('destroy', self.on_destroy)
        self.featurefn = _alist(self.features, feature)

        # Results list
        self.panarea = hildon.PannableArea()
        self.musiclist = MusicList()
        self.musiclist.connect('row-activated', self.row_activated)
        self.panarea.add(self.musiclist)

        self.idmap = {}
        self.items = []

        self.add(self.panarea)

        self.create_menu()

        self.start_feature_fetcher()

    def start_feature_fetcher(self):
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None
        self.fetcher = Fetcher(self.featurefn, self,
                               on_item = self.on_feature_result,
                               on_ok = self.on_feature_complete,
                               on_fail = self.on_feature_complete)
        self.fetcher.start()

    def on_feature_result(self, wnd, item):
        if wnd is self:
            self.musiclist.add_items([item])
            self.idmap[item.ID] = item
            self.items.append(item)

    def on_feature_complete(self, wnd, error=None):
        if wnd is self:
            if error:
                banner = hildon.hildon_banner_show_information(self, '', "Unable to get list")
                banner.set_timeout(2000)
            self.fetcher.stop()
            self.fetcher = None

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
            self.start_tag_fetcher(item.ID)

    def start_tag_fetcher(self, item_id):
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None
        self.fetcher = Fetcher(lambda: jamaendo.get_tag_tracks(item_id),
                               self,
                               on_item = self.on_tag_result,
                               on_ok = self.on_tag_complete,
                               on_fail = self.on_tag_complete)
        self.fetcher.taglist = []
        self.fetcher.start()
        banner = hildon.hildon_banner_show_information(self, '', "Getting tracks for tag")
        banner.set_timeout(2000)

    def on_tag_result(self, wnd, item):
        if wnd is self:
            self.fetcher.taglist.append(item)

    def on_tag_complete(self, wnd, error=None):
        if wnd is self:
            taglist = self.fetcher.taglist
            self.fetcher.stop()
            if not error:
                wnd = open_playerwindow()
                wnd.play_tracks(taglist)
            else:
                banner = hildon.hildon_banner_show_information(self, '', "Error getting tracks")
                banner.set_timeout(2000)
            self.fetcher = None


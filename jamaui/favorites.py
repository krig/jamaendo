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
try:
    import hildon
except:
    import helldon as hildon
import jamaendo
from playerwindow import open_playerwindow
from showartist import ShowArtist
from showalbum import ShowAlbum
from settings import settings
import logging
from fetcher import Fetcher
import itertools

from albumlist import MusicList

log = logging.getLogger(__name__)

def _alist(l, match):
    for key, value in l:
        if key == match:
            return value
    return None

class FavoritesWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Favorites")
        self.connect('destroy', self.on_destroy)
        self.fetcher = None
        self.idmap = {}

        self.panarea = hildon.PannableArea()
        self.favorites = MusicList()
        self.favorites.connect('row-activated', self.row_activated)
        self.panarea.add(self.favorites)
        self.add(self.panarea)

        if not settings.user:
            self.favorites.loading_message = """give your username
to the settings dialog
favorites appear
"""
        else:
            self.favorites.loading_message = """Loading favorites"""

        self.start_favorites_fetcher()

    def on_destroy(self, wnd):
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None

    def start_favorites_fetcher(self):
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None

        def gen():
            generated = []
            for item in jamaendo.favorite_albums(settings.user):
                generated.append(item.ID)
                yield item
            fav = [f[1] for f in settings.favorites \
                       if isinstance(f, tuple) and \
                       len(f) == 2 and \
                       f[0] == 'album' and \
                       f[1] not in generated]
            for item in jamaendo.get_albums(fav):
                yield item

        self.fetcher = Fetcher(gen,
                               self,
                               on_item = self.on_favorites_result,
                               on_ok = self.on_favorites_complete,
                               on_fail = self.on_favorites_complete)
        self.fetcher.start()

    def on_favorites_result(self, wnd, item):
        if wnd is self:
            if item.ID not in self.idmap:
                self.idmap[item.ID] = item
                self.favorites.add_items([item])

    def on_favorites_complete(self, wnd, error=None):
        if wnd is self:
            self.fetcher.stop()
            self.fetcher = None

    def get_item_text(self, item):
        if isinstance(item, jamaendo.Album):
            return "%s - %s" % (item.artist_name, item.name)
        elif isinstance(item, jamaendo.Track):
            return "%s - %s" % (item.artist_name, item.name)
        else:
            return item.name

    def row_activated(self, treeview, path, view_column):
        _id = self.favorites.get_item_id(path)
        item = self.idmap.get(_id)
        if item:
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

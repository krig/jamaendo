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
from albumlist import AlbumList

class ShowArtist(hildon.StackableWindow):
    def __init__(self, artist):
        hildon.StackableWindow.__init__(self)
        self.set_title(artist.name)
        self.artist = artist

        self.panarea = hildon.PannableArea()
        vbox = gtk.VBox(False, 0)

        self.albums = AlbumList()
        self.albums.show_artist(False)
        self.albums.connect('row-activated', self.row_activated)

        self.panarea.add(self.albums)
        vbox.pack_start(self.panarea, True, True, 0)
        self.add(vbox)

        for album in jamaendo.get_albums(artist.ID):
            self.albums.add_album(album)

    def row_activated(self, treeview, path, view_column):
        _id = self.albums.get_album_id(path)
        album = jamaendo.get_album(_id)
        if isinstance(album, list):
            album = album[0]
        self.open_item(album)

    def open_item(self, item):
        if isinstance(item, jamaendo.Album):
            from showalbum import ShowAlbum
            wnd = ShowAlbum(item)
            wnd.show_all()
        elif isinstance(item, jamaendo.Artist):
            wnd = ShowArtist(item)
            wnd.show_all()
        elif isinstance(item, jamaendo.Track):
            wnd = open_playerwindow()
            wnd.play_tracks([item])

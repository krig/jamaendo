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
from settings import settings
import logging

from albumlist import AlbumList

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

        if settings.user:
            # Results list
            self.panarea = hildon.PannableArea()
            self.results = AlbumList()
            self.results.connect('row-activated', self.row_activated)
            self.panarea.add(self.results)

            self.idmap = {}

            def add_album(ID, album_factory):
                if ID not in self.idmap:
                    album = album_factory()
                    self.idmap[ID] = album
                    self.results.add_album(album)

            try:
                for item in jamaendo.favorite_albums(settings.user):
                    add_album(item.ID, lambda: item)
            except jamaendo.JamendoAPIException, e:
                msg = "Query failed, is the user name '%s' correct?" % (settings.user)
                banner = hildon.hildon_banner_show_information(self, '',
                                                               msg)
                banner.set_timeout(3000)

            for item in settings.favorites:
                try:
                    if isinstance(item, tuple) and len(item) == 2:
                        ftype, fid = item
                        if ftype == 'album':
                            add_album(fid, lambda: jamaendo.get_album(fid))

                except jamaendo.JamendoAPIException, e:
                    log.exception("jamaendo.get_album(%s)"%(fid))

            self.add(self.panarea)

        else:
            vbox = gtk.VBox()
            lbl = gtk.Label()
            lbl.set_markup("""<span size="xx-large">jamendo.com
in the settings dialog
enter your username</span>
""")
            lbl.set_single_line_mode(False)
            vbox.pack_start(lbl, True, False)
            self.add(vbox)

    def get_item_text(self, item):
        if isinstance(item, jamaendo.Album):
            return "%s - %s" % (item.artist_name, item.name)
        elif isinstance(item, jamaendo.Track):
            return "%s - %s" % (item.artist_name, item.name)
        else:
            return item.name

    def make_button(self, text, subtext, callback):
        button = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                               hildon.BUTTON_ARRANGEMENT_VERTICAL)
        button.set_text(text, subtext)

        if callback:
            button.connect('clicked', callback)

        #image = gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_BUTTON)
        #button.set_image(image)
        #button.set_image_position(gtk.POS_RIGHT)

        return button

    def row_activated(self, treeview, path, view_column):
        _id = self.results.get_album_id(path)
        item = self.idmap[_id]
        #print _id, item
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

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
import os
import gtk
try:
    import hildon
except:
    import helldon as hildon
import jamaendo
from playerwindow import open_playerwindow
from albumlist import AlbumList
from postoffice import postoffice
import util
import gobject
from playlists import add_to_playlist, show_banner
from fetcher import Fetcher

import logging

log = logging.getLogger(__name__)

class ShowArtist(hildon.StackableWindow):
    ICON_SIZE = 200

    def __init__(self, artist):
        hildon.StackableWindow.__init__(self)
        self.connect('destroy', self.on_destroy)
        self.set_title(artist.name)
        self.artist = artist

        self.connect('destroy', self.on_destroy)
        self.fetcher = None

        top_hbox = gtk.HBox()
        self.image = gtk.Image()
        self.default_pixbuf = util.find_resource('album.png')
        self.image.set_from_pixbuf(self.get_default_pixbuf())

        self.panarea = hildon.PannableArea()
        vbox = gtk.VBox(False, 0)

        self.albums = AlbumList()
        self.albums.loading_message = "No albums"
        self.albums.empty_message = "No albums"
        self.albums.show_artist(False)
        self.albums.connect('row-activated', self.row_activated)

        self.panarea.add(self.albums)
        vbox.pack_start(self.panarea, True, True, 0)
        #self.add(vbox)

        #imgalign = gtk.Alignment(xalign=0.2, yalign=0.4, xscale=1.0)
        #alignment.add(bbox)

        self.image.set_alignment(0.5, 0.0)

        top_hbox.pack_start(self.image, False)
        top_hbox.pack_start(vbox)

        self.add(top_hbox)

        self.albumlist = []

        postoffice.connect('images', self, self.on_images)

        if self.artist.image:
            postoffice.notify('request-images', [self.artist.image])

        self.create_menu()
        self.start_album_fetcher()

    def on_destroy(self, wnd):
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None

    def start_album_fetcher(self):
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None
        self.fetcher = Fetcher(lambda: jamaendo.get_albums(self.artist.ID), self,
                               on_item = self.on_album_result,
                               on_ok = self.on_album_complete,
                               on_fail = self.on_album_complete)
        self.fetcher.start()

    def on_album_result(self, wnd, item):
        if wnd is self:
            self.albums.add_album(item)
            self.albumlist.append(item)

    def on_album_complete(self, wnd, error=None):
        if wnd is self:
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
        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Add to playlist")
        player.connect("clicked", self.on_add_to_playlist)
        self.menu.append(player)
        self.menu.show_all()
        self.set_app_menu(self.menu)

    def on_add_to_playlist(self, button, user_data=None):
        if self.albumlist:
            try:
                tracklist = []
                for album in self.albumlist:
                    tracklist.extend(jamaendo.get_tracks(album.ID))
                add_to_playlist(self, tracklist)
            except jamaendo.JamendoAPIException:
                log.exception("Failed to get track list for artist %s", self.artist.ID)
        else:
            show_banner(self, "Error when opening track list")

    def get_pixbuf(self, img):
        try:
            return gtk.gdk.pixbuf_new_from_file_at_size(img,
                                                        self.ICON_SIZE,
                                                        self.ICON_SIZE)
        except gobject.GError:
            log.error("Broken image in cache: %s", img)
            try:
                os.unlink(img)
            except OSError, e:
                log.warning("Failed to unlink broken image.")
            if img != self.default_pixbuf:
                return self.get_default_pixbuf()
            else:
                return None

    def get_default_pixbuf(self):
        if self.default_pixbuf:
            return self.get_pixbuf(self.default_pixbuf)

    def on_images(self, images):
        for url, image in images:
            if url == self.artist.image:
                pb = self.get_pixbuf(image)
                if pb:
                    self.image.set_from_pixbuf(pb)

    def on_destroy(self, wnd):
        postoffice.disconnect('images', self)

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

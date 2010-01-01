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
from settings import settings
from postoffice import postoffice
import util
import logging
from albumlist import TrackList
import webbrowser

log = logging.getLogger(__name__)

class ShowAlbum(hildon.StackableWindow):
    def __init__(self, album):
        hildon.StackableWindow.__init__(self)
        self.set_title(album.artist_name)
        self.album = album

        self.connect('destroy', self.on_destroy)

        top_hbox = gtk.HBox()
        vbox1 = gtk.VBox()
        self.cover = gtk.Image()
        self.bbox = gtk.HButtonBox()
        self.bbox.set_property('layout-style', gtk.BUTTONBOX_SPREAD)
        self.goto_artist = self.make_imagebutton('artist', self.on_goto_artist)
        self.download = self.make_imagebutton('download', self.on_download)
        self.favorite = self.make_imagebutton('favorite', self.on_favorite)
        self.license = self.make_imagebutton('license', self.on_license)
        self.playbtn = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        self.playbtn.set_label("Play album")
        self.playbtn.set_border_width(0)
        self.playbtn.connect('clicked', self.on_play)

        vbox2 = gtk.VBox()
        self.albumname = gtk.Label()
        self.albumname.set_markup('<big>%s</big>'%(album.name))
        self.trackarea = hildon.PannableArea()

        self.tracks = TrackList(numbers=True)
        self.tracks.connect('row-activated', self.row_activated)

        for track in jamaendo.get_tracks(album.ID):
            self.tracks.add_track(track)

        top_hbox.pack_start(vbox1, False)
        top_hbox.pack_start(vbox2, True)
        vbox1.pack_start(self.cover, True)
        vbox1.pack_start(self.playbtn, False)
        vbox1.pack_start(self.bbox, False)
        self.bbox.add(self.goto_artist)
        self.bbox.add(self.download)
        self.bbox.add(self.favorite)
        self.bbox.add(self.license)
        vbox2.pack_start(self.albumname, False)
        vbox2.pack_start(self.trackarea, True)
        self.trackarea.add(self.tracks)

        self.add(top_hbox)

        postoffice.connect('album-cover', self.on_album_cover)
        postoffice.notify('request-album-cover', self.album.ID, 300)

        self.show_all()

    def on_destroy(self, wnd):
        postoffice.disconnect('album-cover', self.on_album_cover)

    def on_album_cover(self, albumid, size, cover):
        if albumid == self.album.ID and size == 300:
            self.cover.set_from_file(cover)

    def make_imagebutton(self, name, cb):
        btn = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        btn.set_relief(gtk.RELIEF_NONE)
        img = util.find_resource('icon_%s.png'%(name))
        if img:
            btn.set_image(gtk.image_new_from_file(img))
        else:
            btn.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_SMALL_TOOLBAR))
        btn.set_border_width(0)
        btn.connect('clicked', cb)
        return btn

    def on_goto_artist(self, btn):
        artist = jamaendo.get_artist(int(self.album.artist_id))
        self.open_item(artist)

    def on_download(self, btn):
        banner = hildon.hildon_banner_show_information(self, '', "Opening in web browser")
        banner.set_timeout(2000)
        url = self.album.torrent_url()
        webbrowser.open_new(url)

    def on_favorite(self, btn):
        settings.favorite(self.album)
        banner = hildon.hildon_banner_show_information(self, '', "Favorite added")
        banner.set_timeout(2000)


    def on_license(self, btn):
        banner = hildon.hildon_banner_show_information(self, '', "Opening in web browser")
        banner.set_timeout(2000)
        url = self.album.license_url
        webbrowser.open_new(url)

    def on_play(self, btn):
        self.open_item(self.album)

    def row_activated(self, treeview, path, view_column):
        _id = self.tracks.get_track_id(path)
        log.debug("clicked %s", _id)

    def open_item(self, item):
        if isinstance(item, jamaendo.Album):
            tracks = jamaendo.get_tracks(item.ID)
            if tracks:
                wnd = open_playerwindow()
                wnd.play_tracks(tracks)
        elif isinstance(item, jamaendo.Artist):
            from showartist import ShowArtist
            wnd = ShowArtist(item)
            wnd.show_all()
        elif isinstance(item, jamaendo.Track):
            wnd = open_playerwindow()
            wnd.play_tracks([item])

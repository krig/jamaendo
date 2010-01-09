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
import cgi
try:
    import hildon
except:
    import helldon as hildon
import jamaendo
from player import Playlist
from playerwindow import open_playerwindow
from settings import settings
from postoffice import postoffice
import util
import logging
import thread
import gobject
from albumlist import TrackList
from fetcher import Fetcher

import webbrowser

log = logging.getLogger(__name__)

class ShowPlaylist(hildon.StackableWindow):
    def __init__(self, plname, playlist):
        hildon.StackableWindow.__init__(self)
        self.set_title(plname)
        self.playlist_name = plname
        self.playlist = playlist
        self.fetcher = None

        self.connect('destroy', self.on_destroy)

        top_hbox = gtk.HBox()
        vbox1 = gtk.VBox()
        self.cover = gtk.Image()
        tmp = util.find_resource('album.png')
        if tmp:
            self.cover.set_from_file(tmp)

        vbox2 = gtk.VBox()
        self.trackarea = hildon.PannableArea()
        self.tracks = TrackList(numbers=True)
        self.tracks.connect('row-activated', self.row_activated)
        self.tracklist = []

        top_hbox.pack_start(vbox1, False)
        top_hbox.pack_start(vbox2, True)
        vbox1.pack_start(self.cover, True)
        vbox2.pack_start(self.trackarea, True)
        self.trackarea.add(self.tracks)

        self.add(top_hbox)

        postoffice.connect('album-cover', self, self.on_album_cover)
        if len(self.playlist) > 0:
            postoffice.notify('request-album-cover', int(self.playlist[0].album_id), 300)

        self.create_menu()
        self.start_track_fetcher()

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
        player.set_label("Delete playlist")
        player.connect("clicked", self.on_delete_pl)
        self.menu.append(player)
        self.menu.show_all()
        self.set_app_menu(self.menu)

    def on_destroy(self, wnd):
        postoffice.disconnect('album-cover', self)
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None

    def start_track_fetcher(self):
        if self.fetcher:
            self.fetcher.stop()
            self.fetcher = None
        self.fetcher = Fetcher(lambda: self.playlist, self,
                               on_item = self.on_track_result,
                               on_ok = self.on_track_complete,
                               on_fail = self.on_track_complete)
        self.fetcher.start()

    def on_track_result(self, wnd, item):
        if wnd is self:
            self.tracklist.append(item)
            self.tracks.add_track(item)

    def on_track_complete(self, wnd, error=None):
        if wnd is self:
            self.fetcher.stop()
            self.fetcher = None

    def on_delete_pl(self, btn):
        note = hildon.hildon_note_new_confirmation(self, "Do you want to delete '%s' ?" % (self.playlist_name))
        response = note.run()
        note.destroy()
        print response
        if response == gtk.RESPONSE_OK:
            settings.delete_playlist(self.playlist_name)
            settings.save()
            self.destroy()

    def on_album_cover(self, albumid, size, cover):
        if size == 300:
            self.cover.set_from_file(cover)

    def on_play(self, btn):
        self.open_item(self.album)

    def row_activated(self, treeview, path, view_column):
        # TODO: wait for all tracks to load
        _id = self.tracks.get_track_id(path)
        pl = Playlist(self.playlist)
        pl.jump_to(_id)
        wnd = open_playerwindow()
        wnd.show_all()
        wnd.play_tracks(pl)

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

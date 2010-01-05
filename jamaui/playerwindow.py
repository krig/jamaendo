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
import gobject
try:
    import hildon
except:
    import helldon as hildon
import util
import pango
import jamaendo
from settings import settings
from postoffice import postoffice
from player import Playlist, the_player
import logging
import cgi

from songposition import SongPosition
from listbox import ListDialog
import colors
log = logging.getLogger(__name__)

class PlayerWindow(hildon.StackableWindow):
    instance = None

    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("jamaendo")

        PlayerWindow.instance = self

        self.connect('destroy', self.on_destroy)

        self.player = the_player
        self.playlist = the_player.playlist

        vbox = gtk.VBox(False, 8)

        hbox = gtk.HBox(False)

        self.cover = gtk.Image()
        self.set_default_cover()

        vbox2 = gtk.VBox()

        self.playlist_pos = gtk.Label()
        self.playlist_pos.set_alignment(1.0,0)
        self.track = gtk.Label()
        self.track.set_alignment(0,1)
        self.track.set_ellipsize(pango.ELLIPSIZE_END)
        self.artist = gtk.Label()
        self.artist.set_alignment(0,0.5)
        self.artist.set_ellipsize(pango.ELLIPSIZE_END)
        self.album = gtk.Label()
        self.album.set_alignment(0,0)
        self.album.set_ellipsize(pango.ELLIPSIZE_END)
        self.progress = SongPosition()

        self.set_labels('', '', '', 0, 0)

        self._position_timer = None

        vbox2.pack_start(self.playlist_pos, False)
        vbox2.pack_start(self.track, True)
        vbox2.pack_start(self.artist, True)
        vbox2.pack_start(self.album, True)
        vbox2.pack_start(self.progress, False, True)

        hbox.set_border_width(8)
        hbox.pack_start(self.cover, False, True, 8)
        hbox.pack_start(vbox2, True, True, 0)

        vbox.pack_start(hbox, True, True, 0)

        btns = gtk.HButtonBox()
        btns.set_property('layout-style', gtk.BUTTONBOX_SPREAD)

        vbox.pack_start(btns, False, True, 0)

        self.add_stock_button(btns, gtk.STOCK_MEDIA_PREVIOUS, self.on_prev)
        self.add_play_button(btns)
        self.add_stock_button(btns, gtk.STOCK_MEDIA_STOP, self.on_stop)
        self.add_stock_button(btns, gtk.STOCK_MEDIA_NEXT, self.on_next)

        self.add(vbox)

        postoffice.connect('album-cover', self, self.set_album_cover)
        postoffice.connect(['next', 'prev', 'play', 'pause', 'stop'], self, self.on_state_changed)

        self.on_state_changed()

        self.create_menu()

    def create_menu(self):
        self.menu = hildon.AppMenu()

        def to_artist(*args):
            from showartist import ShowArtist
            track = self.playlist.current()
            artist = jamaendo.get_artist(int(track.artist_id))
            wnd = ShowArtist(artist)
            wnd.show_all()
        def to_album(*args):
            from showalbum import ShowAlbum
            track = self.playlist.current()
            album = jamaendo.get_album(int(track.album_id))
            wnd = ShowAlbum(album)
            wnd.show_all()

        b = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        b.set_label("Artist")
        b.connect("clicked", to_artist)
        self.menu.append(b)

        b = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        b.set_label("Album")
        b.connect("clicked", to_album)
        self.menu.append(b)

        b = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        b.set_label("Add to playlist")
        b.connect("clicked", self.on_add_to_playlist)
        self.menu.append(b)

        self.menu.show_all()
        self.set_app_menu(self.menu)

    def on_state_changed(self, *args):
        self.update_state()
        self.update_play_button()

        if self.player.playing():
            self.start_position_timer()
        else:
            self.stop_position_timer()


    def get_album_id(self):
        if self.player.playlist and self.player.playlist.current():
            c = self.player.playlist.current()
            if not c.album_id:
                c.load()
            if c.album_id:
                return c.album_id
        return None

    def on_destroy(self, wnd):
        PlayerWindow.instance = None
        self.stop_position_timer()
        postoffice.disconnect(['album-cover', 'next', 'prev', 'play', 'stop'], self)

    def add_stock_button(self, btns, stock, cb):
        btn = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_focus_on_click(False)
        sz = gtk.ICON_SIZE_BUTTON
        btn.set_image(gtk.image_new_from_stock(stock, sz))
        btn.connect('clicked', cb)
        btns.add(btn)

    def add_play_button(self, btns):
        sz = gtk.ICON_SIZE_BUTTON
        self.playimg = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, sz)
        self.pauseimg = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, sz)
        btn = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        btn.set_relief(gtk.RELIEF_NONE)
        if self.player.playing():
            btn.set_image(self.pauseimg)
            btn.set_data('state', 'pause')
        else:
            btn.set_image(self.playimg)
            btn.set_data('state', 'play')
        btn.connect('clicked', self.on_play)
        btns.add(btn)
        self.playbtn = btn

    def update_play_button(self):
        if self.player.playing():
            self.playbtn.set_image(self.pauseimg)
            self.playbtn.set_data('state', 'pause')
        else:
            self.playbtn.set_image(self.playimg)
            self.playbtn.set_data('state', 'play')

    def set_labels(self, track, artist, album, playlist_pos, playlist_size):

        if self.playlist.radio_mode:
            ppstr = '<span size="small">Radio: %s</span>'%(cgi.escape(self.playlist.radio_name))
        else:
            ppstr = '<span font_desc="%s" foreground="%s">Track %s of %s</span>'%(colors.SmallSystemFont(), colors.SecondaryTextColor(), int(playlist_pos)+1, playlist_size)
        self.playlist_pos.set_markup(ppstr)
        self.track.set_markup('<span font_desc="%s">%s</span>'%(colors.LargeSystemFont(), cgi.escape(track)))
        self.artist.set_markup('%s'%(cgi.escape(artist)))
        self.album.set_markup('<span foreground="%s">%s</span>'%(colors.SecondaryTextColor(), cgi.escape(album)))

    def show_banner(self, message, timeout = 2000):
        banner = hildon.hildon_banner_show_information(self, '', message)
        banner.set_timeout(2000)

    def on_add_to_playlist(self, button, user_data=None):
        track = self.player.playlist.current()
        from playlists import add_to_playlist
        add_to_playlist(self, track)

    def volume_changed_hildon(self, widget):
        settings.volume = widget.get_level()/100.0

    def mute_toggled(self, widget):
        if widget.get_mute():
            settings.volume = 0
        else:
            settings.volume = widget.get_level()/100.0

    def on_position_timeout(self):
        if the_player.playing():
            self.set_song_position(*the_player.get_position_duration())
        else:
            log.debug("position timeout, but not playing")
        return True

    def start_position_timer(self):
        if self._position_timer is not None:
            self.stop_position_timer()
        self._position_timer = gobject.timeout_add(1000, self.on_position_timeout)

    def stop_position_timer(self):
        if self._position_timer is not None:
            gobject.source_remove(self._position_timer)
            self._position_timer = None

    def clear_position(self):
        self.progress.set_position(0)

    def set_song_position(self, time_elapsed, total_time):
        value = (float(time_elapsed) / float(total_time)) if total_time else 0
        self.progress.set_position(value)

    def set_default_cover(self):
        tmp = util.find_resource('album.png')
        if tmp:
            log.debug("Setting cover to %s", tmp)
            self.cover.set_from_file(tmp)

    def update_state(self):
        item = self.playlist.current()
        if item:
            if not item.name:
                item.load()
            self.set_labels(item.name, item.artist_name, item.album_name,
                            self.playlist.current_index(), self.playlist.size())
            self.set_default_cover()
            postoffice.notify('request-album-cover', int(item.album_id), 300)
        else:
            self.set_labels('', '', '', 0, 0)
            self.set_default_cover()

    def set_album_cover(self, albumid, size, cover):
        if size == 300:
            playing = self.get_album_id()
            if playing and albumid and (int(playing) == int(albumid)):
                log.debug("Setting cover to %s", cover)
                self.cover.set_from_file(cover)

    def play_radio(self, radio_name, radio_id):
        playlist = Playlist([])
        playlist.radio_mode = True
        playlist.radio_name = radio_name
        playlist.radio_id = radio_id
        playlist.add(jamaendo.get_radio_tracks(playlist.radio_id))
        log.debug("Playing radio: %s", playlist)
        self.__play_tracks(playlist)
        log.debug("Playlist current: %s, playing? %s",
                  playlist.current_index(),
                  self.player.playing())

    def play_tracks(self, tracks):
        self.__play_tracks(tracks)

    def __play_tracks(self, tracks):
        self.clear_position()
        if isinstance(tracks, Playlist):
            self.playlist = tracks
        else:
            self.playlist = Playlist(tracks)
        log.debug("Playing: %s", self.playlist)
        self.player.stop()
        self.player.play(self.playlist)

    def on_play(self, button):
        if not self.player.playing():
            self.player.play(self.playlist)
        else:
            self.player.pause()
    def on_prev(self, button):
        self.player.prev()

    def on_next(self, button):
        self.player.next()

    def on_stop(self, button):
        self.clear_position()
        self.player.stop()

def open_playerwindow():
    if PlayerWindow.instance:
        player = PlayerWindow.instance
        stack = player.get_stack()
        sz = stack.size()
        windows = stack.pop(sz)
        windows.remove(player)
        windows.append(player)
        stack.push_list(windows)
    else:
        player = PlayerWindow()
        player.show_all()
    return player

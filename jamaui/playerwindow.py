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
import hildon
from settings import settings
from postoffice import postoffice
from player import Playlist, the_player
import logging

log = logging.getLogger(__name__)

class PlayerWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("jamaendo")

        self.connect('destroy', self.on_destroy)

        self.player = the_player
        self.playlist = the_player.playlist

        vbox = gtk.VBox()

        hbox = gtk.HBox()

        self.cover = gtk.Image()
        self.cover.set_from_stock(gtk.STOCK_CDROM, gtk.ICON_SIZE_DIALOG)

        vbox2 = gtk.VBox()

        self.playlist_pos = gtk.Label()
        self.track = gtk.Label()
        self.progress = hildon.GtkHScale()
        self.progress.set_draw_value(False)
        self.progress.set_range(0.0, 1.0)
        self.artist = gtk.Label()
        self.album = gtk.Label()

        self.set_labels('', '', '', 0, 0)

        self._position_timer = None

        vbox2.pack_start(self.track, True)
        vbox2.pack_start(self.artist, False)
        vbox2.pack_start(self.album, False)
        vbox2.pack_start(self.playlist_pos, False)
        vbox2.pack_start(self.progress, False)

        hbox.pack_start(self.cover, True, True, 0)
        hbox.pack_start(vbox2, True, True, 0)

        vbox.pack_start(hbox, True, True, 0)

        btns = gtk.HButtonBox()
        btns.set_property('layout-style', gtk.BUTTONBOX_SPREAD)

        vbox.pack_end(btns, False, True, 0)

        self.add_stock_button(btns, gtk.STOCK_MEDIA_PREVIOUS, self.on_prev)
        self.add_play_button(btns)
        self.add_stock_button(btns, gtk.STOCK_MEDIA_STOP, self.on_stop)
        self.add_stock_button(btns, gtk.STOCK_MEDIA_NEXT, self.on_next)

        self.volume = hildon.VVolumebar()
        self.volume.set_property('can-focus', False)
        self.volume.connect('level_changed', self.volume_changed_hildon)
        self.volume.connect('mute_toggled', self.mute_toggled)
        #self.__gui_root.main_window.connect( 'key-press-event',
        #                                     self.on_key_press )
        hbox.pack_start(self.volume, False)
        self.add(vbox)

        postoffice.connect('album-cover', self, self.set_album_cover)

        #print "Created player window, playlist: %s" % (self.playlist)

        self.update_state()
        self.update_play_button()

    def get_album_id(self):
        if self.playlist and self.playlist.current_index() > -1:
            return self.playlist.current().album_id
        return None

    def on_destroy(self, wnd):
        self.stop_position_timer()
        postoffice.disconnect('album-cover', self)

    def add_stock_button(self, btns, stock, cb):
        btn = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        btn.set_relief(gtk.RELIEF_NONE)
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
        self.playlist_pos.set_markup('<span size="small">%s/%s songs</span>'%(playlist_pos, playlist_size))
        self.track.set_markup('<span size="x-large">%s</span>'%(track))
        self.artist.set_markup('<span size="large">%s</span>'%(artist))
        self.album.set_markup('<span foreground="#aaaaaa">%s</span>'%(album))


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
        self.progress.set_value(0)

    def set_song_position(self, time_elapsed, total_time):
        value = (float(time_elapsed) / float(total_time)) if total_time else 0
        self.progress.set_value( value )

    def update_state(self):
        item = self.playlist.current()
        if item:
            if not item.name:
                item.load()
            #print "current:", item
            self.set_labels(item.name, item.artist_name, item.album_name,
                            self.playlist.current_index(), self.playlist.size())
            postoffice.notify('request-album-cover', int(item.album_id), 300)
            #jamaendo.get_album_cover_async(album_cover_receiver, int(item.album_id), size=200)
            #coverfile = jamaendo.get_album_cover(int(item.album_id), size=200)
            #print "coverfile:", coverfile
            #self.cover.set_from_file(coverfile)

    def set_album_cover(self, albumid, size, cover):
        if size == 300:
            playing = self.get_album_id()
            if int(playing) == int(albumid):
                self.cover.set_from_file(cover)

    def play_tracks(self, tracks):
        self.stop_position_timer()
        self.clear_position()
        self.playlist = Playlist(tracks)
        self.player.stop()
        self.player.play(self.playlist)
        self.update_state()
        self.update_play_button()

    def on_play(self, button):
        if not self.player.playing():
            self.player.play(self.playlist)
            self.start_position_timer()
            self.update_state()
            self.update_play_button()
        else:
            self.stop_position_timer()
            self.player.pause()
            self.update_state()
            self.update_play_button()
    def on_prev(self, button):
        self.player.prev()
        self.update_state()
    def on_next(self, button):
        self.player.next()
        self.update_state()
    def on_stop(self, button):
        self.stop_position_timer()
        self.clear_position()
        self.player.stop()
        self.update_play_button()

def open_playerwindow():
    player = PlayerWindow()
    player.show_all()
    return player

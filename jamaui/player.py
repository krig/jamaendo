# Implements playback controls
# Gstreamer stuff mostly snibbed from Panucci
#
# This file is part of Panucci.
# Copyright (c) 2008-2009 The Panucci Audiobook and Podcast Player Project
#
# Panucci is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Panucci is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Panucci.  If not, see <http://www.gnu.org/licenses/>.
#

import logging
import pygst
pygst.require('0.10')
import gst
import util
import dbus

import jamaendo
from settings import settings
from postoffice import postoffice

log = logging.getLogger(__name__)

class _Player(object):
    """Defines the internal player interface"""
    def __init__(self):
        pass
    def play_url(self, filetype, uri):
        raise NotImplemented
    def playing(self):
        raise NotImplemented
    def play_pause_toggle(self):
        self.pause() if self.playing() else self.play()
    def play(self):
        raise NotImplemented
    def pause(self):
        raise NotImplemented
    def stop(self):
        raise NotImplemented
    def set_eos_callback(self, cb):
        raise NotImplemented

class GStreamer(_Player):
    """Wraps GStreamer"""
    STATES = { gst.STATE_NULL    : 'stopped',
               gst.STATE_PAUSED  : 'paused',
               gst.STATE_PLAYING : 'playing' }

    def __init__(self):
        _Player.__init__(self)
        self.time_format = gst.Format(gst.FORMAT_TIME)
        self.player = None
        self.filesrc = None
        self.filesrc_property = None
        self.volume_control = None
        self.volume_multiplier = 1.
        self.volume_property = None
        self.eos_callback = lambda: self.stop()
        postoffice.connect('settings-changed', self, self.on_settings_changed)

    def on_settings_changed(self, key, value):
        if key == 'volume':
            self._set_volume_level(value)
        #postoffice.disconnect(self)


    def play_url(self, filetype, uri):
        if None in (filetype, uri):
            self.player = None
            return False

        _first = False
        if self.player is None:
            _first = True
            if False:
                self._maemo_setup_playbin2_player(uri)
                log.debug('Using playbin2 (maemo)')
            elif util.platform == 'maemo':
                self._maemo_setup_playbin_player()
                log.debug('Using playbin (maemo)')
            else:
                self._setup_playbin_player()
                log.debug( 'Using playbin (non-maemo)' )

            bus = self.player.get_bus()
            bus.add_signal_watch()
            bus.connect('message', self._on_message)
            self._set_volume_level(settings.volume)

        self._set_uri_to_be_played(uri)

        self.play()
        return True

    def get_state(self):
        if self.player:
            state = self.player.get_state()[1]
            return self.STATES.get(state, 'none')
        return 'none'

    def get_position_duration(self):
        try:
            pos_int = self.player.query_position(self.time_format, None)[0]
            dur_int = self.player.query_duration(self.time_format, None)[0]
        except Exception, e:
            log.exception('Error getting position')
            pos_int = dur_int = 0
        return pos_int, dur_int

    def playing(self):
        return self.get_state() == 'playing'

    def play(self):
        if self.player:
            self.player.set_state(gst.STATE_PLAYING)

    def pause(self):
        if self.player:
            self.player.set_state(gst.STATE_PAUSED)

    def stop(self, reset = True):
        if self.player:
            self.player.set_state(gst.STATE_NULL)
            if reset:
                self.player = None

    def _maemo_setup_playbin2_player(self, url):
        self.player = gst.parse_launch("playbin2 uri=%s" % (url,))
        self.filesrc = self.player
        self.filesrc_property = 'uri'
        self.volume_control = self.player
        self.volume_multiplier = 1.
        self.volume_property = 'volume'

    def _maemo_setup_playbin_player( self):
        self.player = gst.element_factory_make('playbin2', 'player')
        self.filesrc = self.player
        self.filesrc_property = 'uri'
        self.volume_control = self.player
        self.volume_multiplier = 1.
        self.volume_property = 'volume'
        return True

    def _setup_playbin_player( self ):
        """ This is for situations where we have a normal (read: non-maemo)
        version of gstreamer like on a regular linux distro. """
        self.player = gst.element_factory_make('playbin2', 'player')
        self.filesrc = self.player
        self.filesrc_property = 'uri'
        self.volume_control = self.player
        self.volume_multiplier = 1.
        self.volume_property = 'volume'

    def _on_decoder_pad_added(self, decoder, src_pad, sink_pad):
        # link the decoder's new "src_pad" to "sink_pad"
        src_pad.link( sink_pad )

    def _get_volume_level(self):
        if self.volume_control is not None:
            vol = self.volume_control.get_property( self.volume_property )
            return  vol / float(self.volume_multiplier)

    def _set_volume_level(self, value):
        assert  0 <= value <= 1

        if self.volume_control is not None:
            vol = value * float(self.volume_multiplier)
            log.debug("Setting volume to %s", vol)
            self.volume_control.set_property( self.volume_property, vol )

    def _set_uri_to_be_played(self, uri):
        # Sets the right property depending on the platform of self.filesrc
        if self.player is not None:
            self.filesrc.set_property(self.filesrc_property, uri)
            log.info("%s", uri)

    def _on_message(self, bus, message):
        t = message.type

        if t == gst.MESSAGE_EOS:
            log.debug("Gstreamer: End of stream")
            self.eos_callback()
        elif t == gst.MESSAGE_STATE_CHANGED:
            if (message.src == self.player and
                message.structure['new-state'] == gst.STATE_PLAYING):
                log.debug("gstreamer: state -> playing")
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            log.critical( 'Error: %s %s', err, debug )
            self.stop()

    def set_eos_callback(self, cb):
        self.eos_callback = cb

if util.platform == 'maemo':
    class OssoPlayer(_Player):
        """
        A player which uses osso-media-player for playback (Maemo-specific)
        """

        SERVICE_NAME         = "com.nokia.osso_media_server"
        OBJECT_PATH          = "/com/nokia/osso_media_server"
        AUDIO_INTERFACE_NAME = "com.nokia.osso_media_server.music"

        def __init__(self):
            self._on_eos = lambda: self.stop()
            self._state = 'none'
            self._audio = self._init_dbus()
            self._init_signals()

        def play_url(self, filetype, uri):
            self._audio.play_media(uri)

        def playing(self):
            return self._state == 'playing'

        def play_pause_toggle(self):
            self.pause() if self.playing() else self.play()

        def play(self):
            self._audio.play()

        def pause(self):
            if self.playing():
                self._audio.pause()

        def stop(self):
            self._audio.stop()

        def set_eos_callback(self, cb):
            self._on_eos = cb


        def _init_dbus(self):
            session_bus = dbus.SessionBus()
            oms_object = session_bus.get_object(self.SERVICE_NAME,
                                                self.OBJECT_PATH,
                                                introspect = False,
                                                follow_name_owner_changes = True)
            return dbus.Interface(oms_object, self.AUDIO_INTERFACE_NAME)

        def _init_signals(self):
            error_signals = {
                "no_media_selected":            "No media selected",
                "file_not_found":               "File not found",
                "type_not_found":               "Type not found",
                "unsupported_type":             "Unsupported type",
                "gstreamer":                    "GStreamer Error",
                "dsp":                          "DSP Error",
                "device_unavailable":           "Device Unavailable",
                "corrupted_file":               "Corrupted File",
                "out_of_memory":                "Out of Memory",
                "audio_codec_not_supported":    "Audio codec not supported"
            }

            # Connect status signals
            self._audio.connect_to_signal( "state_changed",
                                                self._on_state_changed )
            self._audio.connect_to_signal( "end_of_stream",
                                                lambda x: self._call_eos() )

            # Connect error signals
            for error, msg in error_signals.iteritems():
                self._audio.connect_to_signal(error, lambda *x: self._error(msg))

        def _error(self, msg):
            log.error(msg)

        def _call_eos(self):
            self._on_eos()

        def _on_state_changed(self, state):
            states = ("playing", "paused", "stopped")
            self.__state = state if state in states else 'none'

#    PlayerBackend = OssoPlayer
#else:
PlayerBackend = GStreamer

class Playlist(object):
    def __init__(self, items = []):
        self.radio_mode = False
        self.radio_id = None
        self.radio_name = None
        if items is None:
            items = []
        for item in items:
            assert(isinstance(item, jamaendo.Track))
        self.items = items
        self._current = -1

    def add(self, item):
        if isinstance(item, list):
            for i in item:
                assert(isinstance(i, jamaendo.Track))
            self.items.extend(item)
        else:
            self.items.append(item)

    def next(self):
        if self.has_next():
            self._current = self._current + 1
            return self.items[self._current]
        return None

    def prev(self):
        if self.has_prev():
            self._current = self._current - 1
            return self.items[self._current]
        return None

    def has_next(self):
        return self._current < (len(self.items)-1)

    def has_prev(self):
        return self._current > 0

    def current(self):
        if self._current >= 0:
            return self.items[self._current]
        return None

    def jump_to(self, item_id):
        for c, i in enumerate(self.items):
            if i.ID == item_id:
                self._current = c

    def current_index(self):
        return self._current

    def size(self):
        return len(self.items)

    def __repr__(self):
        return "Playlist(%d of %s)"%(self._current, ", ".join([str(item.ID) for item in self.items]))

class Player(object):
    def __init__(self):
        self.backend = PlayerBackend()
        self.backend.set_eos_callback(self._on_eos)
        self.playlist = Playlist()
        self.__in_end_notify = False # ugly...

    def get_position_duration(self):
        return self.backend.get_position_duration()

    def play(self, playlist = None):
        if playlist:
            self.playlist = playlist
        elif self.playlist is None:
            self.playlist = Playlist()
        if self.playlist.size():
            if self.playlist.current():
                entry = self.playlist.current()
                self.backend.play_url('mp3', entry.mp3_url())
                log.debug("playing %s", entry)
            elif self.playlist.has_next():
                entry = self.playlist.next()
                self.backend.play_url('mp3', entry.mp3_url())
                log.debug("playing %s", entry)
            postoffice.notify('play', entry)

    def pause(self):
        self.backend.pause()
        postoffice.notify('pause', self.playlist.current())

    def stop(self):
        self.backend.stop()
        postoffice.notify('stop', self.playlist.current())

    def playing(self):
        return self.backend.playing()

    def next(self):
        if self.playlist.has_next():
            self.backend.stop(reset=False)
            entry = self.playlist.next()
            self.backend.play_url('mp3', entry.mp3_url())
            log.debug("playing %s", entry)
            postoffice.notify('next', entry)
        elif not self.__in_end_notify:
            self.__in_end_notify = True
            postoffice.notify('playlist-end', self.playlist)
            self.__in_end_notify = False
            # if the notification refills the playlist,
            # we do nothing after this point so we don't
            # mess things up
            if not self.playlist.has_next():
                self.stop()

    def prev(self):
        if self.playlist.has_prev():
            self.backend.stop(reset=False)
            entry = self.playlist.prev()
            self.backend.play_url('mp3', entry.mp3_url())
            log.debug("playing %s", entry)
            postoffice.notify('prev', entry)

    def _on_eos(self):
        self.next()

the_player = Player() # the player instance

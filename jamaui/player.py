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
import dbus.service

import jamaendo

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
        self.volume_multiplier = 1
        self.volume_property = None
        self.eos_callback = lambda: self.stop()

    def play_url(self, filetype, uri):
        if None in (filetype, uri):
            self.player = None
            return False

        log.debug("Setting up for %s : %s", filetype, uri)

        # On maemo use software decoding to workaround some bugs their gst:
        # 1. Weird volume bugs in playbin when playing ogg or wma files
        # 2. When seeking the DSPs sometimes lie about the real position info
        if True:
            self._maemo_setup_playbin_player(uri)
        elif util.platform == 'maemo':
            if not self._maemo_setup_hardware_player(filetype):
                self._maemo_setup_software_player()
                log.debug( 'Using software decoding (maemo)' )
            else:
                log.debug( 'Using hardware decoding (maemo)' )
        else:
            # This is for *ahem* "normal" versions of gstreamer
            self._setup_playbin_player()
            log.debug( 'Using playbin (non-maemo)' )

        self._set_uri_to_be_played(uri)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_message)

        self._set_volume_level( 1 )

        self.play()
        return True

    def get_state(self):
        if self.player:
            state = self.player.get_state()[1]
            return self.STATES.get(state, 'none')
        return 'none'

    def playing(self):
        return self.get_state() == 'playing'

    def play(self):
        if self.player:
            log.debug("playing")
            self.player.set_state(gst.STATE_PLAYING)

    def pause(self):
        if self.player:
            self.player.set_state(gst.STATE_PAUSED)

    def stop(self):
        if self.player:
            self.player.set_state(gst.STATE_NULL)
            self.player = None

    def _maemo_setup_playbin_player(self, url):
        self.player = gst.parse_launch("playbin2 uri=%s" % (url,))
        self.filesrc = self.player
        self.filesrc_property = 'uri'
        self.volume_control = self.player
        self.volume_multiplier = 1.
        self.volume_property = 'volume'

    def _maemo_setup_hardware_player( self, filetype ):
        """ Setup a hardware player for mp3 or aac audio using
        dspaacsink or dspmp3sink """

        if filetype in [ 'mp3', 'aac', 'mp4', 'm4a' ]:
            self.player = gst.element_factory_make('playbin', 'player')
            self.filesrc = self.player
            self.filesrc_property = 'uri'
            self.volume_control = self.player
            self.volume_multiplier = 10.
            self.volume_property = 'volume'
            return True
        else:
            return False

    def _maemo_setup_software_player( self ):
        """
        Setup a software decoding player for maemo, this is the only choice
        for decoding wma and ogg or if audio is to be piped to a bluetooth
        headset (this is because the audio must first be decoded only to be
        re-encoded using sbcenc.
        """

        self.player = gst.Pipeline('player')
        src = gst.element_factory_make('gnomevfssrc', 'src')
        decoder = gst.element_factory_make('decodebin', 'decoder')
        convert = gst.element_factory_make('audioconvert', 'convert')
        resample = gst.element_factory_make('audioresample', 'resample')
        sink = gst.element_factory_make('dsppcmsink', 'sink')

        self.filesrc = src # pointer to the main source element
        self.filesrc_property = 'location'
        self.volume_control = sink
        self.volume_multiplier = 1
        self.volume_property = 'fvolume'

        # Add the various elements to the player pipeline
        self.player.add( src, decoder, convert, resample, sink )

        # Link what can be linked now, the decoder->convert happens later
        gst.element_link_many( src, decoder )
        gst.element_link_many( convert, resample, sink )

        # We can't link the two halves of the pipeline until it comes
        # time to start playing, this singal lets us know when it's time.
        # This is because the output from decoder can't be determined until
        # decoder knows what it's decoding.
        decoder.connect('pad-added',
                        self._on_decoder_pad_added,
                        convert.get_pad('sink') )

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
            vol = value * self.volume_multiplier
            self.volume_control.set_property( self.volume_property, vol )

    def _set_uri_to_be_played(self, uri):
        # Sets the right property depending on the platform of self.filesrc
        if self.player is not None:
            self.filesrc.set_property(self.filesrc_property, uri)

    def _on_message(self, bus, message):
        t = message.type

        if t == gst.MESSAGE_EOS:
            self.eos_callback()
            log.info("End of stream")
        elif t == gst.MESSAGE_STATE_CHANGED:
            old, new, pending = message.parse_state_changed()
            log.info("State changed: %s -> %s -> %s", old, new, pending)
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            log.critical( 'Error: %s %s', err, debug )
            self.stop()
        else:
            log.info("? %s", message.type)

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

    def has_next(self):
        return self._current < (len(self.items)-1)

    def current(self):
        if self._current >= 0:
            return self.items[self._current]
        return None

    def current_index(self):
        return self._current

    def __len__(self):
        return len(self.items)

class Player(Playlist):
    def __init__(self):
        self.backend = PlayerBackend()
        self.backend.set_eos_callback(self._on_eos)
        self.playlist = None

    def play(self, playlist = None):
        if playlist:
            self.playlist = playlist
        if self.playlist is not None:
            if self.playlist.has_next():
                entry = self.playlist.next()
                log.debug("playing %s", entry)
                self.backend.play_url('mp3', entry.mp3_url())

    def pause(self):
        self.backend.pause()

    def stop(self):
        self.backend.stop()

    def playing(self):
        return self.backend.playing()

    def next(self):
        if self.playlist.has_next():
            self.stop()
            self.play()
        else:
            self.stop()

    def prev(self):
        pass

    def _on_eos(self):
        log.debug("EOS!")
        self.next()

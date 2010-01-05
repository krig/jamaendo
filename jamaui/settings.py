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
import cPickle, os
import logging
import jamaendo
import datetime

from postoffice import postoffice

VERSION = 1
log = logging.getLogger(__name__)

class Settings(object):
    defaults = {
        'volume':0.1,
        'user':None,
        'favorites':set([]), # local favorites - until we can sync back
        'playlists':{},
        }

    def __init__(self):
        self.__savename = "/tmp/jamaendo_uisettings"
        for k,v in self.defaults.iteritems():
            setattr(self, k, v)

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if key in self.defaults.keys():
            postoffice.notify('settings-changed', key, value)

    def set_filename(self, savename):
        self.__savename = savename

    def favorite(self, album):
        self.favorites.add(('album', album.ID))
        self.save()
        postoffice.notify('settings-changed', 'favorites', self.favorites)

    def get_playlist(self, playlist, get_track_objects=True):
        entry = self.playlists.get(playlist)
        if entry:
            if get_track_objects:
                return [jamaendo.Track(item['id'], item['data']) for item in entry]
            return entry
        return None

    def add_to_playlist(self, playlist, track):
        if isinstance(track, jamaendo.Track):
            track = {'id':track.ID, 'data':track.get_data()}
        assert(isinstance(track, dict))
        lst = self.playlists.get(playlist)
        if not lst:
            lst = []
            self.playlists[playlist] = lst
        lst.append(track)
        postoffice.notify('settings-changed', 'playlists', self.playlists)
        log.debug("playlists is now %s", self.playlists)

    def load(self):
        if not os.path.isfile(self.__savename):
            return
        try:
            f = open(self.__savename)
            settings = cPickle.load(f)
            f.close()

            if settings['version'] > VERSION:
                log.warning("Settings version %s higher than current version (%s)",
                            settings['version'], VERSION)

            for k in self.defaults.keys():
                if k in settings:
                    if k == 'playlists' and not isinstance(k, dict):
                        continue
                    setattr(self, k, settings[k])
            print settings
        except Exception, e:
            log.exception('failed to load settings')

    def save(self):
        try:
            settings = {
                'version':VERSION,
                }
            for k in self.defaults.keys():
                settings[k] = getattr(self, k)
            f = open(self.__savename, 'w')
            cPickle.dump(settings, f)
            f.close()
            print settings
        except Exception, e:
            log.exception('failed to save settings')

settings = Settings()

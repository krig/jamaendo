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
# console interface to jamaui/jamaendo

# debugging hack - add . to path
import os, sys
local_module_dir = os.path.join(os.path.dirname(sys.argv[0]), '..')
if os.path.isdir(local_module_dir):
    sys.path.append(local_module_dir)

import jamaendo
from jamaui.player import Player, Playlist, the_player
import time
import gobject

gobject.threads_init()

import pprint

pp = pprint.PrettyPrinter(indent=4)

#pp.pprint(stuff)

class Console(object):
    def run(self):
        query = sys.argv[1]

        queries = ['albums_of_the_week', 'artists', 'albums']
        if query in queries:
            getattr(self, "query_"+query)()
        else:
            print "Valid queries: " + ", ".join(queries)

    def query_albums_of_the_week(self):
        result = jamaendo.albums_of_the_week()
        pp.pprint([(a.ID, a.name) for a in result])
        for a in result:
            self.play_album(a)

    def query_artists(self):
        result = jamaendo.search_artists(sys.argv[2])
        pp.pprint([(a.ID, a.name) for a in result])
        for a in result:
            albums = jamaendo.get_albums(a.ID)
            for album in albums:
                print "Playing album: %s - %s" % (a.name, album.name)
                self.play_album(album)

    def query_albums(self):
        result = jamaendo.search_albums(sys.argv[2])
        pp.pprint([(a.ID, a.name) for a in result])
        for a in result:
            self.play_album(a)

    def play_tracks(self, tracks):
        playlist = Playlist(tracks)
        player = the_player
        player.play(playlist)

        while player.playing():
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                player.next()

    def play_album(self, album):
        if not album.tracks:
            album.load()
        print "%s - %s" % (album.artist_name, album.name)
        if album.tracks:
            self.play_tracks(album.tracks)

if __name__=="__main__":
    main()

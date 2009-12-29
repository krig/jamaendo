# console interface to jamaui/jamaendo

# debugging hack - add . to path
import os, sys
local_module_dir = os.path.join(os.path.dirname(sys.argv[0]), '..')
if os.path.isdir(local_module_dir):
    sys.path.append(local_module_dir)

from jamaendo.api import LocalDB, Query, Queries, refresh_dump
from jamaui.player import Player, Playlist
import time

class Refresher(object):
    def __init__(self):
        self.done = False
        self.last_percent = 0
        print "Preparing local database..."
    def complete(self):
        self.done = True
    def progress(self, percent):
        if percent - self.last_percent >= 5:
            print "\r%d%%" % (percent),
            self.last_percent = percent

    def run(self):
        refresh_dump(self.complete, self.progress, force=False)
        while not self.done:
            time.sleep(1)


def pprint(x):
    import json
    print json.dumps(x, sort_keys=True, indent=4)

class Console(object):
    def run(self):
        Refresher().run()

        query = sys.argv[1]

        queries = ['today',
                   'tracks_this_month',
                   'artist',
                   'album',
                   'play_track',
                   'play_album']
        if query in queries:
            getattr(self, "query_"+query)()
        else:
            print "Valid queries: " + ", ".join(queries)

    def query_today(self):
        result = Queries.albums_today()
        pprint(result)

    def query_tracks_this_month(self):
        result = Queries.tracks_this_month()
        pprint(result)

    def query_artist(self):
        q = sys.argv[2]
        db = LocalDB()
        db.connect()
        for artist in db.search_artists(q):
            pprint(artist)

    def query_album(self):
        q = sys.argv[2]
        db = LocalDB()
        db.connect()
        for album in db.search_albums(q):
            print "%s: %s - %s" % (album['id'], album['artist'], album['name'])

    def query_play_track(self):
        trackid = int(sys.argv[2])
        uri = Query.track_mp3(trackid)
        items = [uri]
        playlist = Playlist(items)
        player = Player()
        player.play(playlist)

    def query_play_album(self):
        albumid = int(sys.argv[2])
        db = LocalDB()
        db.connect()
        album = None
        for a in db.get_albums([albumid]):
            album = a
            break
        if not album:
            return
        print "%s - %s" % (album['artist'], album['name'])
        items = [Query.track_mp3(int(track['id'])) for track in album['tracks']]

        playlist = Playlist(items)
        player = Player()
        player.play(playlist)

        while player.playing():
            time.sleep(1)

if __name__=="__main__":
    main()

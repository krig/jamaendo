#!/usr/bin/env python
#
# This file is part of Jamaendo.
# Copyright (c) 2010, Kristoffer Gronlund
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# An improved, structured jamendo API wrapper for the N900 with cacheing
# Image / cover downloads.. and more?
import urllib, threading, os, time, simplejson, re
import logging, hashlib

_CACHEDIR = None
_COVERDIR = None
_GET2 = '''http://api.jamendo.com/get2/'''
_MP3URL = _GET2+'stream/track/redirect/?id=%d&streamencoding=mp31'
_OGGURL = _GET2+'stream/track/redirect/?id=%d&streamencoding=ogg2'
_TORRENTURL = _GET2+'bittorrent/file/redirect/?album_id=%d&type=archive&class=mp32'

try:
    log = logging.getLogger(__name__)
except:
    class StdoutLogger(object):
        def info(self, s, *args):
            print s % (args)
        def debug(self, s, *args):
            pass#print s % (args)
    log = StdoutLogger()

# These classes can be partially constructed,
# and if asked for a property they don't know,
# makes a query internally to get the full story

_ARTIST_FIELDS = ['id', 'name', 'image']
_ALBUM_FIELDS = ['id', 'name', 'image', 'artist_name', 'artist_id', 'license_url']
_TRACK_FIELDS = ['id', 'name', 'image', 'artist_id', 'artist_name', 'album_name', 'album_id', 'numalbum', 'duration']
_RADIO_FIELDS = ['id', 'name', 'idstr', 'image']

class LazyQuery(object):
    def set_from_json(self, json):
        for key, value in json.iteritems():
            if key == 'id':
                assert(self.ID == int(value))
            else:
                if key.endswith('_id'):
                    value = int(value)
                setattr(self, key, value)

    def load(self):
        """Not automatic for now,
        will have to do artist.load()

        This is filled in further down
        in the file
        """
        raise NotImplemented

    def _needs_load(self):
        return True

    def _set_from(self, other):
        raise NotImplemented

    def _needs_load_impl(self, *attrs):
        for attr in attrs:
            if getattr(self, attr) is None:
                return True
        return False

    def _set_from_impl(self, other, *attrs):
        for attr in attrs:
            self._set_if(other, attr)

    def _set_if(self, other, attrname):
        if getattr(self, attrname) is None and getattr(other, attrname) is not None:
            setattr(self, attrname, getattr(other, attrname))

    def __repr__(self):
        try:
            return u"%s(%s)"%(self.__class__.__name__,
                              u", ".join(("%s:%s"%(k,repr(v))) for k,v in self.__dict__.iteritems() if not k.startswith('_')))
        except UnicodeEncodeError:
            #import traceback
            #traceback.print_exc()
            return u"%s(?)"%(self.__class__.__name__)

class Artist(LazyQuery):
    def __init__(self, ID, json=None):
        self.ID = int(ID)
        self.name = None
        self.image = None
        self.albums = None # None means not downloaded
        if json:
            self.set_from_json(json)

    def _needs_load(self):
        return self._needs_load_impl('name', 'albums')

    def _set_from(self, other):
        return self._set_from_impl(other, 'name', 'image', 'albums')

class Album(LazyQuery):
    def __init__(self, ID, json=None):
        self.ID = int(ID)
        self.name = None
        self.image = None
        self.artist_name = None
        self.artist_id = None
        self.license_url = None
        self.tracks = None # None means not downloaded
        if json:
            self.set_from_json(json)

    def torrent_url(self):
        return _TORRENTURL%(self.ID)


    def _needs_load(self):
        return self._needs_load_impl('name', 'image', 'artist_name', 'artist_id', 'license_url', 'tracks')

    def _set_from(self, other):
        return self._set_from_impl(other, 'name', 'image', 'artist_name', 'artist_id', 'license_url', 'tracks')

class Track(LazyQuery):
    def __init__(self, ID, json=None):
        self.ID = int(ID)
        self.name = None
        self.image = None
        self.artist_id = None
        self.artist_name = None
        self.album_name = None
        self.album_id = None
        self.numalbum = None
        self.duration = None
        if json:
            self.set_from_json(json)

    def mp3_url(self):
       return _MP3URL%(self.ID)

    def ogg_url(self):
       return _OGGURL%(self.ID)

    def _needs_load(self):
        return self._needs_load_impl('name', 'artist_name', 'artist_id', 'album_name', 'album_id', 'numalbum', 'duration')

    def _set_from(self, other):
        return self._set_from_impl(other, 'name', 'image', 'artist_name', 'artist_id', 'album_name', 'album_id', 'numalbum', 'duration')

class Radio(LazyQuery):
    def __init__(self, ID, json=None):
        self.ID = int(ID)
        self.name = None
        self.idstr = None
        self.image = None
        if json:
            self.set_from_json(json)

    def _needs_load(self):
        return self._needs_load_impl('name', 'idstr', 'image')

    def _set_from(self, other):
        return self._set_from_impl(other, 'name', 'idstr', 'image')


_artists = {} # id -> Artist()
_albums = {} # id -> Album()
_tracks = {} # id -> Track()
_radios = {} # id -> Radio()


# cache sizes per session (TODO)
_CACHED_ARTISTS = 100
_CACHED_ALBUMS = 200
_CACHED_TRACKS = 500
_CACHED_RADIOS = 10
# cache sizes, persistant
_CACHED_COVERS = 2048

# TODO: cache queries?

class Query(object):
    rate_limit = 1.1 # seconds between queries
    last_query = time.time() - 1.5

    @classmethod
    def _ratelimit(cls):
        now = time.time()
        if now - cls.last_query < cls.rate_limit:
            time.sleep(cls.rate_limit - (now - cls.last_query))
        cls.last_query = now

    def __init__(self):
        pass

    def _geturl(self, url):
        log.info("%s", url)
        Query._ratelimit()
        try:
            f = urllib.urlopen(url)
            ret = simplejson.load(f)
            f.close()
        except Exception, e:
            return None
        return ret

    def __str__(self):
        return "#%s" % (self.__class__.__name__)

    def execute(self):
        raise NotImplemented

class CoverFetcher(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.cond = threading.Condition()
        self.work = []

    def _fetch_cover(self, albumid, size):
        try:
            coverdir = _COVERDIR if _COVERDIR else '/tmp'
            to = os.path.join(coverdir, '%d-%d.jpg'%(albumid, size))
            if not os.path.isfile(to):
                url = _GET2+'image/album/redirect/?id=%d&imagesize=%d'%(albumid, size)
                urllib.urlretrieve(url, to)
            return to
        except Exception, e:
            return None

    def _fetch_image(self, url):
        try:
            h = hashlib.md5(url).hexdigest()
            coverdir = _COVERDIR if _COVERDIR else '/tmp'
            to = os.path.join(coverdir, h+'.jpg')
            if not os.path.isfile(to):
                urllib.urlretrieve(url, to)
            return to
        except Exception, e:
            return None

    def request_cover(self, albumid, size, cb):
        self.cond.acquire()
        self.work.insert(0, (albumid, size, cb))
        self.cond.notify()
        self.cond.release()

    def request_images(self, urls, cb):
        """cb([(url, image)])"""
        self.cond.acquire()
        self.work.insert(0, ('images', urls, cb))
        self.cond.notify()
        self.cond.release()

    def run(self):
        while True:
            work = []
            self.cond.acquire()
            while True:
                work = self.work
                if work:
                    self.work = []
                    break
                self.cond.wait()
            self.cond.release()

            multi = len(work) > 1
            for job in work:
                if job[0] == 'images':
                    self.process_images(job[1], job[2])
                else:
                    self.process_cover(*job)
                if multi:
                    time.sleep(1.0)

    def process_cover(self, albumid, size, cb):
        cover = self._fetch_cover(albumid, size)
        if cover:
            cb(albumid, size, cover)

    def process_images(self, urls, cb):
        results = [(url, image) for url, image in ((url, self._fetch_image(url)) for url in urls) if image is not None]
        if results:
            cb(results)

class CoverCache(object):
    """
    cache and fetch covers
    TODO: background thread that
    fetches and returns covers,
    asynchronously, LIFO
    """
    def __init__(self):
        self._covers = {} # (albumid, size) -> file
        self._images = {}
        self._fetcher = CoverFetcher()
        self._fetcher.start()
        if _COVERDIR and os.path.isdir(_COVERDIR):
            self.prime_cache()

    def prime_cache(self):
        coverdir = _COVERDIR
        covermatch = re.compile(r'(\d+)\-(\d+)\.jpg')

        prev_covers = os.listdir(coverdir)

        if len(prev_covers) > _CACHED_COVERS:
            import random
            dropn = len(prev_covers) - _CACHED_COVERS
            todrop = random.sample(prev_covers, dropn)
            log.warning("Deleting from cache: %s", todrop)
            for d in todrop:
                m = covermatch.match(d)
                if m:
                    try:
                        os.unlink(os.path.join(coverdir, d))
                    except OSError, e:
                        log.exception('unlinking failed')

        for fil in os.listdir(coverdir):
            fl = os.path.join(coverdir, fil)
            m = covermatch.match(fil)
            if m and os.path.isfile(fl):
                self._covers[(int(m.group(1)), int(m.group(2)))] = fl

    def fetch_cover(self, albumid, size):
        coverdir = _COVERDIR
        if coverdir:
            to = os.path.join(coverdir, '%d-%d.jpg'%(albumid, size))
            if not os.path.isfile(to):
                url = _GET2+'image/album/redirect/?id=%d&imagesize=%d'%(albumid, size)
                urllib.urlretrieve(url, to)
                self._covers[(albumid, size)] = to
            return to
        return None

    def get_cover(self, albumid, size):
        cover = self._covers.get((albumid, size), None)
        if not cover:
            cover = self.fetch_cover(albumid, size)
        return cover

    def get_async(self, albumid, size, cb):
        cover = self._covers.get((albumid, size), None)
        if cover:
            cb(albumid, size, cover)
        else:
            def cb2(albumid, size, cover):
                self._covers[(albumid, size)] = cover
                cb(albumid, size, cover)
            self._fetcher.request_cover(albumid, size, cb2)

    def get_images_async(self, url_list, cb):
        found = []
        lookup = []
        for url in url_list:
            image = self._images.get(url, None)
            if image:
                found.append((url, image))
            else:
                lookup.append(url)
        if found:
            cb(found)

        if lookup:
            def cb2(results):
                for url, image in results:
                    self._images[url] = image
                cb(results)
            self._fetcher.request_images(lookup, cb2)

_cover_cache = CoverCache()

def set_cache_dir(cachedir):
    global _CACHEDIR
    global _COVERDIR
    _CACHEDIR = cachedir
    _COVERDIR = os.path.join(_CACHEDIR, 'covers')

    try:
        os.makedirs(_CACHEDIR)
    except OSError:
        pass

    try:
        os.makedirs(_COVERDIR)
    except OSError:
        pass

    _cover_cache.prime_cache()

def get_album_cover(albumid, size=100):
    return _cover_cache.get_cover(albumid, size)

def get_album_cover_async(cb, albumid, size=100):
    _cover_cache.get_async(albumid, size, cb)

def get_images_async(cb, url_list):
    _cover_cache.get_images_async(url_list, cb)

class CustomQuery(Query):
    def __init__(self, url):
        Query.__init__(self)
        self.url = url

    def execute(self):
        return self._geturl(self.url)

    def __str__(self):
        return self.url

class GetQuery(Query):
    queries = {
        'artist' : {
            'url' : _GET2+'+'.join(_ARTIST_FIELDS)+'/artist/json/?',
            'params' : 'artist_id=%d',
            'constructor' : Artist
            },
        'artist_list' : {
            'url' : _GET2+'+'.join(_ALBUM_FIELDS)+'/artist/json/?',
            'params' : 'artist_id=%s',
            'constructor' : Album
            },
        'album' : {
            'url' : _GET2+'+'.join(_ALBUM_FIELDS)+'/album/json/?',
            'params' : 'album_id=%d',
            'constructor' : Album
            },
        'album_list' : {
            'url' : _GET2+'+'.join(_ALBUM_FIELDS)+'/album/json/?',
            'params' : 'album_id=%s',
            'constructor' : Album
            },
        'albums' : {
            'url' : _GET2+'+'.join(_ALBUM_FIELDS)+'/album/json/?',
            'params' : 'artist_id=%d',
            'constructor' : [Album]
            },
        'track' : {
            'url' : _GET2+'+'.join(_TRACK_FIELDS)+'/track/json/track_album+album_artist?',
            'params' : 'id=%d',
            'constructor' : Track
            },
        'track_list' : {
            'url' : _GET2+'+'.join(_TRACK_FIELDS)+'/track/json/track_album+album_artist?',
            'params' : 'id=%s',
            'constructor' : Track
            },
        'tracks' : {
            'url' : _GET2+'+'.join(_TRACK_FIELDS)+'/track/json/track_album+album_artist?',
            'params' : 'order=numalbum_asc&album_id=%d',
            'constructor' : [Track]
            },
        'radio' : {
            'url' : _GET2+'+'.join(_TRACK_FIELDS)+'/track/json/radio_track_inradioplaylist+track_album+album_artist/?',
            'params' : 'order=random_asc&radio_id=%d',
            'constructor' : [Track]
            },
        'favorite_albums' : {
            'url' : _GET2+'+'.join(_ALBUM_FIELDS)+'/album/json/album_user_starred/?',
            'params' : 'user_idstr=%s',
            'constructor' : [Album]
            },
        }

    def __init__(self, what, ID):
        Query.__init__(self)
        self.ID = ID
        info = GetQuery.queries[what]
        self.url = info['url']
        self.params = info['params']
        self.constructor = info['constructor']

    def construct(self, data):
        constructor = self.constructor
        if isinstance(constructor, list):
            constructor = constructor[0]
        if isinstance(data, list):
            return [constructor(int(x['id']), json=x) for x in data]
        else:
            return constructor(int(data['id']), json=data)

    def execute(self):
        js = self._geturl(self.url + self.params % (self.ID))
        if not js:
            return None
        return self.construct(js)

    def __str__(self):
        return self.url + self.params % (self.ID)

class SearchQuery(GetQuery):
    def __init__(self, what, query=None, order=None, user=None, count=10):
        GetQuery.__init__(self, what, None)
        self.query = query
        self.order = order
        self.count = count
        self.user = user

    def execute(self):
        params = {}
        if self.query:
            params['searchquery'] = self.query
        if self.order:
            params['order'] = self.order
        if self.count:
            params['n'] = self.count
        if self.user:
            params['user_idstr'] = self.user
        js = self._geturl(self.url +  urllib.urlencode(params))
        if not js:
            return None
        return self.construct(js)

    def __str__(self):
        params = {'searchquery':self.query, 'order':self.order, 'n':self.count}
        return self.url +  urllib.urlencode(params)

class JamendoAPIException(Exception):
    def __init__(self, url):
        Exception.__init__(self, url)

def _update_cache(cache, new_items):
    if not isinstance(new_items, list):
        new_items = [new_items]
    for item in new_items:
        old = cache.get(item.ID)
        if old:
            old._set_from(item)
        else:
            cache[item.ID] = item
        if isinstance(item, Artist) and item.albums:
            for album in item.albums:
                _update_cache(_albums, album)
        elif isinstance(item, Album) and item.tracks:
            for track in item.tracks:
                _update_cache(_tracks, track)
    # enforce cache limits here!
    # also, TODO: save/load cache between sessions
    # that will require storing a timestamp with
    # each item, though..
    # perhaps,
    # artists: 1 day - changes often
    # albums: 2-5 days - changes less often (?)
    # tracks: 1 week - changes rarely, queried often

def get_artist(artist_id):
    """Returns: Artist"""
    a = _artists.get(artist_id, None)
    if not a:
        q = GetQuery('artist', artist_id)
        a = q.execute()
        if not a:
            raise JamendoAPIException(str(q))
        _update_cache(_artists, a)
        if isinstance(a, list):
            a = a[0]
    return a

def get_artists(artist_ids):
    """Returns: [Artist]"""
    assert(isinstance(artist_ids, list))
    found = []
    lookup = []
    for artist_id in artist_ids:
        a = _artists.get(artist_id, None)
        if not a:
            lookup.append(artist_id)
        else:
            found.append(a)
    if lookup:
        q = GetQuery('artist_list', '+'.join(str(x) for x in lookup))
        a = q.execute()
        if not a:
            raise JamendoAPIException(str(q))
        _update_cache(_artists, a)
        lookup = a
    return found + lookup

def get_album_list(album_ids):
    """Returns: [Album]"""
    assert(isinstance(album_ids, list))
    found = []
    lookup = []
    for album_id in album_ids:
        a = _albums.get(album_id, None)
        if not a:
            lookup.append(album_id)
        else:
            found.append(a)
    if lookup:
        q = GetQuery('album_list', '+'.join(str(x) for x in lookup))
        a = q.execute()
        if not a:
            raise JamendoAPIException(str(q))
        _update_cache(_albums, a)
        lookup = a
    return found + lookup

def get_albums(artist_id):
    """Returns: [Album]
    Parameter can either be an artist_id or a list of album ids.
    """
    if isinstance(artist_id, list):
        return get_album_list(artist_id)
    a = _artists.get(artist_id, None)
    if a and a.albums:
        return a.albums

    q = GetQuery('albums', artist_id)
    a = q.execute()
    if not a:
        raise JamendoAPIException(str(q))
    _update_cache(_artists, a)
    return a

def get_album(album_id):
    """Returns: Album"""
    a = _albums.get(album_id, None)
    if not a:
        q = GetQuery('album', album_id)
        a = q.execute()
        if not a:
            raise JamendoAPIException(str(q))
        _update_cache(_albums, a)
        if isinstance(a, list):
            a = a[0]
    return a

def get_track_list(track_ids):
    """Returns: [Track]"""
    assert(isinstance(track_ids, list))
    found = []
    lookup = []
    for track_id in track_ids:
        a = _tracks.get(track_id, None)
        if not a:
            lookup.append(track_id)
        else:
            found.append(a)
    if lookup:
        q = GetQuery('track_list', '+'.join(str(x) for x in lookup))
        a = q.execute()
        if not a:
            raise JamendoAPIException(str(q))
        _update_cache(_tracks, a)
        lookup = a
    return found + lookup

def get_tracks(album_id):
    """Returns: [Track]
    Parameter can either be an album_id or a list of track ids.
    """
    if isinstance(album_id, list):
        return get_track_list(album_id)
    a = _albums.get(album_id, None)
    if a and a.tracks:
        return a.tracks

    q = GetQuery('tracks', album_id)
    a = q.execute()
    if not a:
        raise JamendoAPIException(str(q))
    _update_cache(_tracks, a)
    return a

def get_track(track_id):
    """Returns: Track"""
    a = _tracks.get(track_id, None)
    if not a:
        q = GetQuery('track', track_id)
        a = q.execute()
        if not a:
            raise JamendoAPIException(str(q))
        _update_cache(_tracks, a)
        if isinstance(a, list):
            a = a[0]
    return a

def get_radio_tracks(radio_id):
    """Returns: [Track]"""
    q = GetQuery('radio', radio_id)
    a = q.execute()
    if not a:
        raise JamendoAPIException(str(q))
    _update_cache(_tracks, a)
    return a

def search_artists(query):
    """Returns: [Artist]"""
    q = SearchQuery('artist', query, 'searchweight_desc')
    a = q.execute()
    if not a:
        raise JamendoAPIException(str(q))
    _update_cache(_artists, a)
    return a

def search_albums(query):
    """Returns: [Album]"""
    q = SearchQuery('album', query, 'searchweight_desc')
    a = q.execute()
    if not a:
        raise JamendoAPIException(str(q))
    _update_cache(_albums, a)
    return a

def search_tracks(query):
    """Returns: [Track]"""
    q = SearchQuery('track', query=query, order='searchweight_desc')
    a = q.execute()
    if not a:
        raise JamendoAPIException(str(q))
    _update_cache(_tracks, a)
    return a

def albums_of_the_week():
    """Returns: [Album]"""
    q = SearchQuery('album', order='ratingweek_desc')
    a = q.execute()
    if not a:
        raise JamendoAPIException(str(q))
    _update_cache(_albums, a)
    return a

def new_releases():
    """Returns: [Track] (playlist)"""
    q = SearchQuery('track', order='releasedate_desc')
    a = q.execute()
    if not a:
        raise JamendoAPIException(str(q))
    _update_cache(_tracks, a)
    return a

def tracks_of_the_week():
    """Returns: [Track] (playlist)"""
    q = SearchQuery('track', order='ratingweek_desc')
    a = q.execute()
    if not a:
        raise JamendoAPIException(str(q))
    _update_cache(_tracks, a)
    return a

def get_radio(radio_id):
    """Returns: Radio"""
    q = CustomQuery(_GET2+"id+name+idstr+image/radio/json?id=%d"%(radio_id))
    js = q.execute()
    if not js:
        raise JamendoAPIException(str(q))
    if isinstance(js, list):
        ks = js[0]
    return Radio(radio_id, json=js)

def starred_radios():
    """Returns: [Radio]"""
    q = CustomQuery(_GET2+"id+name+idstr+image/radio/json?order=starred_desc")
    js = q.execute()
    if not js:
        raise JamendoAPIException(str(q))
    return [Radio(int(radio['id']), json=radio) for radio in js]

def favorite_albums(user):
    """Returns: [Album]"""
    q = SearchQuery('favorite_albums', user=user, count=20)
    a = q.execute()
    if not a:
        raise JamendoAPIException(str(q))
    _update_cache(_albums, a)
    return a

### Set loader functions for classes

def _artist_loader(self):
    if self._needs_load():
        artist = get_artist(self.ID)
        artist.albums = get_albums(self.ID)
        self._set_from(artist)
Artist.load = _artist_loader

def _album_loader(self):
    if self._needs_load():
        album = get_album(self.ID)
        album.tracks = get_tracks(self.ID)
        self._set_from(album)
Album.load = _album_loader

def _track_loader(self):
    track = get_track(self.ID)
    self._set_from(track)
Track.load = _track_loader

def _radio_loader(self):
    radio = get_radio(self.ID)
    self._set_from(radio)
Radio.load = _radio_loader

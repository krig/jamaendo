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
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Jamaendo nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
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
import urllib, threading, os, gzip, time, simplejson, re

_CACHEDIR = None
_COVERDIR = None
_GET2 = '''http://api.jamendo.com/get2/'''
_MP3URL = _GET2+'stream/track/redirect/?id=%d&streamencoding=mp31'
_OGGURL = _GET2+'stream/track/redirect/?id=%d&streamencoding=ogg2'
_TORRENTURL = _GET2+'bittorrent/file/redirect/?album_id=%d&type=archive&class=mp32'

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

# These classes can be partially constructed,
# and if asked for a property they don't know,
# makes a query internally to get the full story

_ARTIST_FIELDS = ['id', 'name', 'image']
_ALBUM_FIELDS = ['id', 'name', 'image', 'artist_name', 'artist_id', 'license_url']
_TRACK_FIELDS = ['id', 'name', 'image', 'artist_name', 'album_name', 'album_id', 'numalbum', 'duration']
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
                              u", ".join(repr(v) for k,v in self.__dict__.iteritems() if not k.startswith('_')))
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
        return self._needs_load_impl('name', 'artist_name', 'album_name', 'album_id', 'numalbum', 'duration')

    def _set_from(self, other):
        return self._set_from_impl(other, 'name', 'image', 'artist_name', 'album_name', 'album_id', 'numalbum', 'duration')

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
        #print "*** %s" % (url)
        Query._ratelimit()
        f = urllib.urlopen(url)
        ret = simplejson.load(f)
        f.close()
        return ret

    def __str__(self):
        return "#%s" % (self.__class__.__name__)

    def execute(self):
        raise NotImplemented

import threading

class CoverFetcher(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.cond = threading.Condition()
        self.work = []

    def _fetch_cover(self, albumid, size):
        coverdir = _COVERDIR if _COVERDIR else '/tmp'
        to = os.path.join(coverdir, '%d-%d.jpg'%(albumid, size))
        if not os.path.isfile(to):
            url = _GET2+'image/album/redirect/?id=%d&imagesize=%d'%(albumid, size)
            urllib.urlretrieve(url, to)
        return to

    def request_cover(self, albumid, size, cb):
        self.cond.acquire()
        self.work.insert(0, (albumid, size, cb))
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
            for albumid, size, cb in work:
                cover = self._fetch_cover(albumid, size)
                cb(albumid, size, cover)
                if multi:
                    time.sleep(1.0)

class CoverCache(object):
    """
    cache and fetch covers
    TODO: background thread that
    fetches and returns covers,
    asynchronously, LIFO
    """
    def __init__(self):
        self._covers = {} # (albumid, size) -> file
        coverdir = _COVERDIR if _COVERDIR else '/tmp'
        if os.path.isdir(coverdir):
            covermatch = re.compile(r'(\d+)\-(\d+)\.jpg')
            for fil in os.listdir(coverdir):
                fl = os.path.join(coverdir, fil)
                m = covermatch.match(fil)
                if m and os.path.isfile(fl):
                    self._covers[(int(m.group(1)), int(m.group(2)))] = fl
        self._fetcher = CoverFetcher()
        self._fetcher.start()

    def fetch_cover(self, albumid, size):
        coverdir = _COVERDIR if _COVERDIR else '/tmp'
        to = os.path.join(coverdir, '%d-%d.jpg'%(albumid, size))
        if not os.path.isfile(to):
            url = _GET2+'image/album/redirect/?id=%d&imagesize=%d'%(albumid, size)
            urllib.urlretrieve(url, to)
            self._covers[(albumid, size)] = to
        return to

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
            self._fetcher.request_cover(albumid, size, cb)

_cover_cache = CoverCache()

def get_album_cover(albumid, size=100):
    return _cover_cache.get_cover(albumid, size)

def get_album_cover_async(cb, albumid, size=100):
    _cover_cache.get_async(albumid, size, cb)

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
        'album' : {
            'url' : _GET2+'+'.join(_ALBUM_FIELDS)+'/album/json/?',
            'params' : 'album_id=%d',
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
    #http://api.jamendo.com/get2/id+name+url+image+artist_name/album/jsonpretty/album_user_starred/?user_idstr=sylvinus&n=all
    #q = SearchQuery('album', user_idstr=user)

        }
#http://api.jamendo.com/get2/id+name+image+artist_name+album_name+album_id+numalbum+duration/track/json/radio_track_inradioplaylist+track_album+album_artist/?order=numradio_asc&radio_id=283

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

def get_albums(artist_id):
    """Returns: [Album]"""
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

def get_tracks(album_id):
    """Returns: [Track]"""
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

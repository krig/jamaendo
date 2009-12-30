import urllib, threading, os, gzip, time, simplejson, re
_DUMP_URL = '''http://img.jamendo.com/data/dbdump_artistalbumtrack.xml.gz'''
_DUMP = os.path.expanduser('''~/.cache/jamaendo/dbdump.xml.gz''')
_DUMP_TMP = os.path.expanduser('''~/.cache/jamaendo/new_dbdump.xml.gz''')

try:
    os.makedirs(os.path.dirname(_DUMP))
except OSError:
    pass

def has_dump():
    return os.path.isfile(_DUMP)

def _file_is_old(fil, old_age):
    return os.path.getmtime(fil) < (time.time() - old_age)

def _dump_is_old():
    return not has_dump() or _file_is_old(_DUMP, 60*60*24) # 1 day

def refresh_dump(complete_callback, progress_callback=None, force=False):
    if force or _dump_is_old():
        downloader = Downloader(complete_callback, progress_callback)
        downloader.start()
    else:
        complete_callback(True)

class Downloader(threading.Thread):
    def __init__(self, complete_callback, progress_callback):
        threading.Thread.__init__(self)
        self.complete_callback = complete_callback
        self.progress_callback = progress_callback

    def actual_callback(self, numblocks, blocksize, filesize):
        if self.progress_callback:
            try:
                percent = min((numblocks*blocksize*100)/filesize, 100)
            except:
                percent = 100
            self.progress_callback(percent)

    def run(self):
        success = True
        try:
            urllib.urlretrieve(_DUMP_URL, _DUMP_TMP, self.actual_callback)
            if os.path.isfile(_DUMP):
                os.remove(_DUMP)
            os.rename(_DUMP_TMP, _DUMP)
        except Exception, e:
            success = False
        self.complete_callback(success)

def fast_iter(context, func):
    for event, elem in context:
        func(elem)
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
    del context

from lxml import etree

class Obj(object):
    def __repr__(self):
        def printable(v):
            if isinstance(v, basestring):
                return v.encode('utf-8')
            else:
                return str(v)
        return "{%s}" % (", ".join("%s=%s"%(k.encode('utf-8'), printable(v)) \
                             for k,v in self.__dict__.iteritems() if not k.startswith('_')))

class LocalDB(object):
    def __init__(self):
        self.fil = None

    def connect(self):
        self.fil = gzip.open(_DUMP)

    def close(self):
        self.fil.close()

    def make_album_brief(self, element):
        ret = {}
        for info in element:
            if info.tag == 'id':
                ret['id'] = int(info.text)
            elif info.tag == 'name':
                ret['name'] = info.text
        return ret

    def make_artist_obj(self, element):
        ret = {}
        for child in element:
            if child.tag == 'id':
                ret['id'] = int(child.text)
            elif child.tag in ('name', 'image'):
                ret[child.tag] = child.text
            elif child.tag == 'Albums':
                ret['albums'] = [self.make_album_brief(a) for a in child]
        return ret

    def make_track_obj(self, element):
        ret = {}
        for info in element:
            if info.tag == 'id':
                _id = int(info.text)
                ret['id'] = _id
                ret['mp3'] = Query.track_mp3(_id)
                ret['ogg'] = Query.track_ogg(_id)
            elif info.tag in ('name', 'numalbum'):
                ret[info.tag] = info.text
        return ret

    def make_album_obj(self, element):
        ret = {}
        artist = element.getparent().getparent()
        if artist is not None:
            for child in artist:
                if child.tag == 'name':
                    ret['artist_name'] = child.text
                elif child.tag == 'id':
                    ret['artist_id'] = int(child.text)
        for child in element:
            if child.tag == 'id':
                ret['id'] = int(child.text)
            elif child.tag in ('name', 'image'):
                if child.text:
                    ret[child.tag] = child.text
                else:
                    ret[child.tag] = ""
            elif child.tag == 'Tracks':
                ret['tracks'] = [self.make_track_obj(t) for t in child]
        return ret

    def artist_walker(self, name_match):
        for event, element in etree.iterparse(self.fil, tag="artist"):
            name = element.xpath('./name')[0].text.lower()
            if name and name.find(name_match) > -1:
                yield self.make_artist_obj(element)
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]
        raise StopIteration

    def album_walker(self, name_match):
        for event, element in etree.iterparse(self.fil, tag="album"):
            name = element.xpath('./name')[0].text
            if name and name.lower().find(name_match) > -1:
                yield self.make_album_obj(element)
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]
        raise StopIteration

    def artistid_walker(self, artistids):
        for event, element in etree.iterparse(self.fil, tag="artist"):
            _id = element.xpath('./id')[0].text
            if _id and int(_id) in artistids:
                yield self.make_artist_obj(element)
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]
        raise StopIteration

    def albumid_walker(self, albumids):
        for event, element in etree.iterparse(self.fil, tag="album"):
            _id = element.xpath('./id')[0].text
            if _id and (int(_id) in albumids):
                yield self.make_album_obj(element)
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]
        raise StopIteration

    def search_artists(self, substr):
        substr = substr.lower()
        return (artist for artist in self.artist_walker(substr))

    def search_albums(self, substr):
        substr = substr.lower()
        return (album for album in self.album_walker(substr))

    def get_artists(self, artistids):
        return (artist for artist in self.artistid_walker(artistids))

    def get_albums(self, albumids):
        return (album for album in self.albumid_walker(albumids))

_GET2 = '''http://api.jamendo.com/get2/'''

class Query(object):
    last_query = time.time()
    caching = True
    cache_time = 60*60*24
    rate_limit = 1.0 # max queries per second

    def __init__(self,
                 select=['id', 'name', 'image', 'artist_name', 'artist_id'],
                 request='album',
                 track=['track_album', 'album_artist']):
        if request == 'track':
            self.url = "%s%s/%s/json/%s" % (_GET2, '+'.join(select), request, '+'.join(track))
        else:
            self.url = "%s%s/%s/json/" % (_GET2, '+'.join(select), request)

    def __call__(self, order=None, count=5, query=None, albumids=None):
        return self.emit(order=order, count=count, query=query, albumids=albumids)

    def emit(self, order=None, count=5, query=None, albumids=None):
        """ratelimited query"""
        self._ratelimit()
        paramdict = {'n':count}
        if order is not None:
            paramdict['order'] = order
        if query is not None:
            paramdict['searchquery'] = query
        if albumids is not None:
            paramdict['album_id'] = " ".join(str(_id) for _id in albumids)
        params = urllib.urlencode(paramdict)
        url = self.url + "?%s" % (params)
        f = urllib.urlopen(url)
        ret = simplejson.load(f)
        f.close()
        return ret

    def _ratelimit(self):
        now = time.time()
        if now - self.last_query < self.rate_limit:
            time.sleep(self.rate_limit - (now - self.last_query))
        self.last_query = now


    @staticmethod
    def album_cover(albumid, size=200):
        to = '~/.cache/jamaendo/cover-%d-%d.jpg'%(albumid, size)
        if not os.path.isfile(to):
            url = _GET2+'image/album/redirect/?id=%d&imagesize=%d'%(albumid, size)
            urllib.urlretrieve(url, to)
        return to

    @staticmethod
    def track_ogg(trackid):
       return _GET2+ 'stream/track/redirect/?id=%d&streamencoding=ogg2'%(trackid)

    @staticmethod
    def track_mp3(trackid):
       return _GET2+ 'stream/track/redirect/?id=%d&streamencoding=mp31'%(trackid)

class Queries(object):
    @staticmethod
    def albums_this_week():
        return Query().emit(order='ratingweek_desc')
    @staticmethod
    def albums_all_time():
        return Query().emit(order='ratingtotal_desc')
    @staticmethod
    def albums_this_month():
        return Query().emit(order='ratingmonth_desc')
    @staticmethod
    def albums_today():
        return Query().emit(order='ratingday_desc')
    @staticmethod
    def playlists_all_time():
        q = Query(select=['id','name', 'user_idstr'], request='playlist')
        return q.emit(order='ratingtotal_desc')

    @staticmethod
    def tracks_this_month():
        q = Query(select=['id', 'name',
                          'stream',
                          'album_name', 'artist_name',
                          'album_id', 'artist_id'],
                  request='track')
        return q.emit(order='ratingmonth_desc')

    @staticmethod
    def search_albums(query):
        q = Query()
        return q.emit(order='searchweight_desc', query=query)

    @staticmethod
    def search_artists(query):
        q = Query(request='artist', select=['id', 'name', 'image'])
        return q.emit(order='searchweight_desc', query=query)

    @staticmethod
    def album_tracks(albumids, select=['id', 'name', 'numalbum']):
        #http://api.jamendo.com/get2/id+name/track/jsonpretty/?album_id=33+46
        q = Query(select=select,
                  request='track')
        ret = q.emit(albumids=albumids, count=100)
        for track in ret:
            track['mp3'] = Query.track_mp3(int(track['id']))
            track['ogg'] = Query.track_ogg(int(track['id']))
        return ret

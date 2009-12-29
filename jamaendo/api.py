import urllib, threading, os, gzip, time, json, re
_DUMP_URL = '''http://img.jamendo.com/data/dbdump_artistalbumtrack.xml.gz'''
_DUMP = os.path.expanduser('''~/.cache/jamaendo/dbdump.xml.gz''')

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
        complete_callback()

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
        urllib.urlretrieve(_DUMP_URL, _DUMP, self.actual_callback)
        self.complete_callback()

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

class DB(object):
    def __init__(self):
        self.fil = None

    def connect(self):
        self.fil = gzip.open(_DUMP)

    def close(self):
        self.fil.close()

    def make_artist_obj(self, element):
        if element.text is not None and element.text != "":
            return element.text
        else:
            ret = {}
            for child in element:
                if child.tag in ['name', 'id', 'image']:
                    ret[child.tag] = child.text
            return ret

    def make_album_obj(self, element):
        if element.text is not None and element.text != "":
            return element.text
        else:
            ret = {}
            for child in element:
                if child.tag in ['name', 'id', 'image']:
                    if child.text:
                        ret[child.tag] = child.text
                    else:
                        ret[child.tag] = ""
                if child.tag == 'Tracks':
                    tracks = []
                    for track in child:
                        trackd = {}
                        for trackinfo in track:
                            if trackinfo.tag in ['name', 'id', 'numalbum']:
                                trackd[trackinfo.tag] = trackinfo.text
                        tracks.append(trackd)
                    ret['tracks'] = tracks
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
            if _id and int(_id) in albumids:
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

    def get_album(self, artistid):
        return (artist for artist in self.artistid_walker(artistid))

    def get_album(self, albumid):
        return (album for album in self.albumid_walker(albumid))

_GET2 = '''http://api.jamendo.com/get2/'''

class Query(object):
    last_query = time.time()

    def __init__(self, order, select=['id', 'name', 'image', 'artist_name'], request='album', track=None, n=8):
        if request == 'track':
            self.url = "%s%s/%s/json/%s?n=%s&order=%s" % (_GET2, '+'.join(select), request, '+'.join(track), n, order)
        else:
            self.url = "%s%s/%s/json/?n=%s&order=%s" % (_GET2, '+'.join(select), request, n, order)

    def emit(self):
        """ratelimited query"""
        now = time.time()
        if now - self.last_query < 1.0:
            time.sleep(1.0 - (now - self.last_query))
        self.last_query = now
        f = urllib.urlopen(self.url)
        ret = json.load(f)
        f.close()
        return ret

class Queries(object):
    albums_this_week = Query(order='ratingweek_desc')
    albums_all_time = Query(order='ratingtotal_desc')
    albums_this_month = Query(order='ratingmonth_desc')
    albums_today = Query(order='ratingday_desc')
    playlists_all_time = Query(select=['id','name', 'user_idstr'], request='playlist', order='ratingtotal_desc')
    tracks_this_month = Query(select=['id', 'name', 'url', 'stream', 'album_name', 'album_url', 'album_id', 'artist_id', 'artist_name'],
                              request='track',
                              track=['track_album', 'album_artist'],
                              order='ratingmonth_desc')

def get_cover(albumid, size=200):
    to = '~/.cache/jamaendo/cover-%d-%d.jpg'%(albumid, size)
    if not os.path.isfile(to):
        url = _GET2+'image/album/redirect/?id=%d&imagesize=%d'%(albumid, size)
        urllib.urlretrieve(url, to)
    return to

def get_ogg_url(trackid):
   return _GET2+ 'stream/track/redirect/?id=%d&streamencoding=ogg2'%(trackid)

def get_mp3_url(trackid):
   return _GET2+ 'stream/track/redirect/?id=%d&streamencoding=mp31'%(trackid)

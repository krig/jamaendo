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

    def make_obj(self, element):
        if element.text is not None and element.text != "":
            return element.text
        else:
            ret = Obj()
            for child in element:
                setattr(ret, child.tag, self.make_obj(child))
            return ret

    def artist_walker(self):
        for event, element in etree.iterparse(self.fil, tag="artist"):
            yield self.make_obj(element)
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]
        raise StopIteration

    def search_artists(self, substr):
        substr = substr.lower()
        #return [dir(artist) for artist in self.artist_walker() if artist.name.find(substr) > -1]
        artist = self.artist_walker().next()
        print artist
        print artist.name
        return [artist.id]

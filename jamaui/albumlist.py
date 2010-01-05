import os
import gtk
import gobject
try:
    import hildon
except:
    import helldon as hildon
import jamaendo
import util
from settings import settings
from postoffice import postoffice
import logging

log = logging.getLogger(__name__)

class _BaseList(gtk.TreeView):
    """
    TODO: unify the different lists into one
    """
    ICON_SIZE = 50

    def __init__(self):
        gtk.TreeView.__init__(self)
        self.__store = None
        self.default_pixbuf = util.find_resource('album.png')
        self.connect('destroy', self.on_destroy)

    def get_pixbuf(self, img):
        try:
            return gtk.gdk.pixbuf_new_from_file_at_size(img,
                                                        self.ICON_SIZE,
                                                        self.ICON_SIZE)
        except gobject.GError:
            log.error("Broken image in cache: %s", img)
            try:
                os.unlink(img)
            except OSError, e:
                log.warning("Failed to unlink broken image.")
            if img != self.default_pixbuf:
                return self.get_default_pixbuf()
            else:
                return None

    def get_default_pixbuf(self):
        if self.default_pixbuf:
            return self.get_pixbuf(self.default_pixbuf)

    def on_destroy(self, wnd):
        pass

class MusicList(_BaseList):
    def __init__(self):
        _BaseList.__init__(self)
        (self.COL_ICON, self.COL_NAME, self.COL_ID, self.COL_IMAGE) = range(4)
        self.__store = gtk.ListStore(gtk.gdk.Pixbuf, str, int, str)

        self.set_model(self.__store)

        icon = gtk.TreeViewColumn('Icon')
        self.append_column(icon)
        cell = gtk.CellRendererPixbuf()
        icon.pack_start(cell, True)
        icon.add_attribute(cell, 'pixbuf', self.COL_ICON)

        col = gtk.TreeViewColumn('Name')
        self.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', self.COL_NAME)
        self.set_search_column(self.COL_NAME)
        col.set_sort_column_id(self.COL_NAME)

        postoffice.connect('images', self, self.on_images)

    def get_item_id(self, path):
        return self.__store.get(self.__store.get_iter(path), self.COL_ID)[0]

    def on_destroy(self, wnd):
        postoffice.disconnect('images', self)

    def on_images(self, images):
        for url, image in images:
            for row in self.__store:
                if row[self.COL_IMAGE] == url:
                    pb = self.get_pixbuf(image)
                    if pb:
                        row[self.COL_ICON] = pb

    def add_items(self, items):
        images = [x for x in (self.get_item_image(item) for item in items) if x]
        for item in items:
            txt = self.get_item_text(item)
            self.__store.append([self.get_default_pixbuf(), txt, item.ID, self.get_item_image(item)])
        if images:
            postoffice.notify('request-images', images)

    def get_item_text(self, item):
        if isinstance(item, jamaendo.Album):
            return "%s - %s" % (item.artist_name, item.name)
        elif isinstance(item, jamaendo.Track):
            return "%s - %s" % (item.artist_name, item.name)
        else:
            return item.name

    def get_item_image(self, item):
        ret = None
        if isinstance(item, jamaendo.Track):
            ret = item.album_image
        elif hasattr(item, 'image'):
            ret = item.image
        if ret:
            ret = ret.replace('1.100.jpg', '1.%d.jpg'%(self.ICON_SIZE))
        return ret

class AlbumList(_BaseList):
    def __init__(self):
        _BaseList.__init__(self)
        (self.COL_ICON, self.COL_NAME, self.COL_ID) = range(3)
        self.__store = gtk.ListStore(gtk.gdk.Pixbuf, str, int)
        self.__show_artist = True

        self.set_model(self.__store)

        icon = gtk.TreeViewColumn('Icon')
        self.append_column(icon)
        cell = gtk.CellRendererPixbuf()
        icon.pack_start(cell, True)
        icon.add_attribute(cell, 'pixbuf', self.COL_ICON)

        col = gtk.TreeViewColumn('Name')
        self.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', self.COL_NAME)
        self.set_search_column(self.COL_NAME)
        col.set_sort_column_id(self.COL_NAME)

        postoffice.connect('album-cover', self, self.on_album_cover)

    def on_destroy(self, wnd):
        _BaseList.on_destroy(self, wnd)
        postoffice.disconnect('album-cover', self)

    def on_album_cover(self, albumid, size, cover):
        if size == self.ICON_SIZE:
            for row in self.__store:
                if row[self.COL_ID] == albumid:
                    row[self.COL_ICON] = self.get_pixbuf(cover)

    def add_album(self, album):
        if self.__show_artist:
            txt = "%s - %s" % (album.artist_name, album.name)
        else:
            txt = album.name
        self.__store.append([self.get_default_pixbuf(), txt, album.ID])
        postoffice.notify('request-album-cover', album.ID, self.ICON_SIZE)

    def get_album_id(self, path):
        return self.__store.get(self.__store.get_iter(path), self.COL_ID)[0]

    def show_artist(self, show):
        self.__show_artist = show

class TrackList(_BaseList):
    def __init__(self, numbers = True):
        _BaseList.__init__(self)
        self.track_numbers = numbers
        self.__store = gtk.ListStore(int, str, int)
        self.set_model(self.__store)

        if numbers:
            col0 = gtk.TreeViewColumn('Num')
            self.append_column(col0)
            cell0 = gtk.CellRendererText()
            col0.pack_start(cell0, True)
            col0.add_attribute(cell0, 'text', 0)

        col = gtk.TreeViewColumn('Name')
        self.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', 1)

        self.set_search_column(1 if numbers else 0)
        col.set_sort_column_id(0)

    def add_track(self, track):
        self.__store.append([track.numalbum, track.name, track.ID])

    def get_track_id(self, path):
        treeiter = self.__store.get_iter(path)
        _, _, _id = self.__store.get(treeiter, 0, 1, 2)
        return _id

class RadioList(_BaseList):
    def __init__(self):
        _BaseList.__init__(self)
        (self.COL_ICON, self.COL_NAME, self.COL_ID, self.COL_IMAGE) = range(4)
        self.__store = gtk.ListStore(gtk.gdk.Pixbuf, str, int, str)
        self.set_model(self.__store)

        icon = gtk.TreeViewColumn('Icon')
        self.append_column(icon)
        cell = gtk.CellRendererPixbuf()
        icon.pack_start(cell, True)
        icon.add_attribute(cell, 'pixbuf', self.COL_ICON)

        col = gtk.TreeViewColumn('Name')
        self.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', self.COL_NAME)
        self.set_search_column(self.COL_NAME)
        col.set_sort_column_id(self.COL_NAME)

        postoffice.connect('images', self, self.on_images)

    def on_destroy(self, wnd):
        postoffice.disconnect('images', self)

    def add_radios(self, radios):
        for radio in radios:
            self.__store.append([self.get_default_pixbuf(), self.radio_name(radio), radio.ID, radio.image])
        postoffice.notify('request-images', [radio.image for radio in radios])


    def get_radio_id(self, path):
        treeiter = self.__store.get_iter(path)
        name, _id = self.__store.get(treeiter, self.COL_NAME, self.COL_ID)
        return name, _id

    def on_images(self, images):
        for url, image in images:
            for row in self.__store:
                if row[self.COL_IMAGE] == url:
                    pb = self.get_pixbuf(image)
                    if pb:
                        row[self.COL_ICON] = pb

    def radio_name(self, radio):
        if radio.idstr:
            return radio.idstr.capitalize()
        elif radio.name:
            return radio.name
        else:
            return "Radio #%s" % (radio.ID)

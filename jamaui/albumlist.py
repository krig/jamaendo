import gtk
import hildon
import jamaendo
from settings import settings
from postoffice import postoffice
import logging

log = logging.getLogger(__name__)

class AlbumList(gtk.TreeView):
    def __init__(self):
        gtk.TreeView.__init__(self)
        self.__store = gtk.ListStore(str, int)
        self.set_model(self.__store)

        col = gtk.TreeViewColumn('Name')
        self.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', 0)
        self.set_search_column(0)
        col.set_sort_column_id(0)

        self.__show_artist = True

    def add_album(self, album):
        if self.__show_artist:
            txt = "%s - %s" % (album.artist_name, album.name)
        else:
            txt = album.name
        self.__store.append([txt, album.ID])

    def get_album_id(self, path):
        treeiter = self.__store.get_iter(path)
        _, _id = self.__store.get(treeiter, 0, 1)
        return _id

    def show_artist(self, show):
        self.__show_artist = show

class TrackList(gtk.TreeView):
    def __init__(self, numbers = True):
        gtk.TreeView.__init__(self)
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

class RadioList(gtk.TreeView):
    def __init__(self):
        gtk.TreeView.__init__(self)
        self.__store = gtk.ListStore(str, int)
        self.set_model(self.__store)

        col = gtk.TreeViewColumn('Name')
        self.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', 0)

        self.set_search_column(0)
        col.set_sort_column_id(0)

    def add_radio(self, radio):
        self.__store.append([self.radio_name(radio), radio.ID])

    def get_radio_id(self, path):
        treeiter = self.__store.get_iter(path)
        _, _id = self.__store.get(treeiter, 0, 1)
        return _id

    def radio_name(self, radio):
        if radio.idstr:
            return radio.idstr.capitalize()
        elif radio.name:
            return radio.name
        else:
            return "Radio #%s" % (radio.ID)

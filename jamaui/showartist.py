import gtk
import hildon
import jamaendo
from playerwindow import open_playerwindow

class ShowArtist(hildon.StackableWindow):
    def __init__(self, artist):
        hildon.StackableWindow.__init__(self)
        self.set_title("Artist")
        self.artist = artist

        self.panarea = hildon.PannableArea()
        vbox = gtk.VBox(False, 0)

        name = gtk.Label()
        name.set_markup('<big>%s</big>'%(artist.name))
        vbox.pack_start(name, False)

        self.album_store = gtk.ListStore(str, int)
        self.album_view = gtk.TreeView(self.album_store)
        col = gtk.TreeViewColumn('Name')
        self.album_view.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', 0)
        self.album_view.set_search_column(0)
        col.set_sort_column_id(0)
        self.album_view.connect('row-activated', self.row_activated)


        self.panarea.add(self.album_view)
        vbox.pack_start(self.panarea, True, True, 0)
        self.add(vbox)

        for album in jamaendo.get_albums(artist.ID):
            self.album_store.append([album.name, album.ID])

    def row_activated(self, treeview, path, view_column):
        treeiter = self.album_store.get_iter(path)
        title, _id = self.album_store.get(treeiter, 0, 1)
        album = jamaendo.get_album(_id)
        if isinstance(album, list):
            album = album[0]
        self.open_item(album)

    def open_item(self, item):
        if isinstance(item, jamaendo.Album):
            from showalbum import ShowAlbum
            wnd = ShowAlbum(item)
            wnd.show_all()
        elif isinstance(item, jamaendo.Artist):
            wnd = ShowArtist(item)
            wnd.show_all()
        elif isinstance(item, jamaendo.Track):
            wnd = open_playerwindow()
            wnd.play_tracks([item])

import gtk
import hildon
import jamaendo
from playerwindow import open_playerwindow
from showartist import ShowArtist
from showalbum import ShowAlbum
from settings import settings
import logging

log = logging.getLogger(__name__)

def _alist(l, match):
    for key, value in l:
        if key == match:
            return value
    return None

class FavoritesWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Favorites")

        if settings.user:
            # Results list
            self.panarea = hildon.PannableArea()
            self.result_store = gtk.ListStore(str, int)
            #self.result_store.append(['red'])
            self.result_view = gtk.TreeView(self.result_store)
            col = gtk.TreeViewColumn('Name')
            self.result_view.append_column(col)
            cell = gtk.CellRendererText()
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', 0)
            self.result_view.set_search_column(0)
            col.set_sort_column_id(0)
            self.result_view.connect('row-activated', self.row_activated)

            self.panarea.add(self.result_view)

            self.idmap = {}
            try:
                for item in jamaendo.favorite_albums(settings.user):
                    self.idmap[item.ID] = item
                    self.result_store.append([self.get_item_text(item), item.ID])
            except jamaendo.JamendoAPIException, e:
                msg = "Query failed, is the user name '%s' correct?" % (settings.user)
                banner = hildon.hildon_banner_show_information(self, '',
                                                               msg)
                banner.set_timeout(3000)


            def add_album(albumid):
                album = jamaendo.get_album(albumid)
                self.idmap[albumid] = album
                self.result_store.append([self.get_item_text(album), albumid])

            for item in settings.favorites:
                try:
                    if isinstance(item, tuple) and len(item) == 2:
                        ftype, fid = item
                        if ftype == 'album':
                            add_album(fid)

                except jamaendo.JamendoAPIException, e:
                    log.exception("jamaendo.get_album(%s)"%(fid))

            self.add(self.panarea)

        else:
            vbox = gtk.VBox()
            lbl = gtk.Label()
            lbl.set_markup("""<span size="xx-large">jamendo.com
in the settings dialog
enter your username</span>
""")
            lbl.set_single_line_mode(False)
            vbox.pack_start(lbl, True, False)
            self.add(vbox)

    def get_item_text(self, item):
        if isinstance(item, jamaendo.Album):
            return "%s - %s" % (item.artist_name, item.name)
        elif isinstance(item, jamaendo.Track):
            return "%s - %s" % (item.artist_name, item.name)
        else:
            return item.name

    def make_button(self, text, subtext, callback):
        button = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                               hildon.BUTTON_ARRANGEMENT_VERTICAL)
        button.set_text(text, subtext)

        if callback:
            button.connect('clicked', callback)

        #image = gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_BUTTON)
        #button.set_image(image)
        #button.set_image_position(gtk.POS_RIGHT)

        return button

    def row_activated(self, treeview, path, view_column):
        treeiter = self.result_store.get_iter(path)
        title, _id = self.result_store.get(treeiter, 0, 1)
        item = self.idmap[_id]
        print _id, item
        self.open_item(item)

    def open_item(self, item):
        if isinstance(item, jamaendo.Album):
            wnd = ShowAlbum(item)
            wnd.show_all()
        elif isinstance(item, jamaendo.Artist):
            wnd = ShowArtist(item)
            wnd.show_all()
        elif isinstance(item, jamaendo.Track):
            wnd = open_playerwindow()
            wnd.play_tracks([item])

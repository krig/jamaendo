import gtk
import hildon
import jamaendo
from playerwindow import open_playerwindow

class RadiosWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Radios")

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

        self.radios = {}
        hildon.hildon_gtk_window_set_progress_indicator(self, 1)
        for item in jamaendo.starred_radios():
            self.radios[item.ID] = item
            self.result_store.append([self.radio_text(item), item.ID])
        hildon.hildon_gtk_window_set_progress_indicator(self, 0)

        self.add(self.panarea)

    def radio_text(self, radio):
        if radio.name and radio.idstr:
            return "%s (%s)" % (radio.name, radio.idstr)
        elif radio.name:
            return radio.name
        elif radio.idstr:
            return radio.idstr
        else:
            return "Radio #%s" % (radio.ID)

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
        item = self.radios[_id]
        print _id, item
        self.open_item(item)

    def open_item(self, item):
        hildon.hildon_gtk_window_set_progress_indicator(self, 1)
        tracks = jamaendo.get_radio_tracks(item.ID)
        hildon.hildon_gtk_window_set_progress_indicator(self, 0)
        if tracks:
            wnd = open_playerwindow()
            wnd.play_tracks(tracks)

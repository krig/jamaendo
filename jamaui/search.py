import gtk
import hildon
import jamaendo
from playerwindow import open_playerwindow

class SearchWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Search")

        vbox = gtk.VBox(False, 0)

        hbox = gtk.HBox()
        self.entry = hildon.Entry(gtk.HILDON_SIZE_FINGER_HEIGHT)
        self.entry.set_placeholder("Search")
        self.entry.connect('activate', self.on_search)
        btn = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        btn.set_label("Go")
        btn.connect('clicked', self.on_search)
        hbox.pack_start(self.entry, True, True, 0)
        hbox.pack_start(btn, False)

        btnbox = gtk.HBox()
        playbtn = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        playbtn.set_label("Play selected")
        playbtn.connect('clicked', self.play_selected)
        btnbox.pack_start(playbtn, False)

        self.results = hildon.TouchSelector(text=True)
        self.results.connect("changed", self.selection_changed)
        self.results.set_column_selection_mode(hildon.TOUCH_SELECTOR_SELECTION_MODE_SINGLE)

        vbox.pack_start(hbox, False)
        vbox.pack_start(self.results, True, True, 0)
        vbox.pack_start(btnbox, False)

        self.add(vbox)

        self.idmap = {}

        self.pwnd = None

    def on_search(self, w):
        txt = self.entry.get_text()
        for album in jamaendo.search_albums(query=txt):
            title = "%s - %s" % (album.artist_name, album.name)
            self.idmap[title] = album
            self.results.append_text(title)

    def selection_changed(self, results, userdata):
        pass

    def play_selected(self, btn):
        current_selection = self.results.get_current_text()

        album = self.idmap[current_selection]
        tracks = jamaendo.get_tracks(album.ID)
        if tracks:
            wnd = open_playerwindow(tracks)
            wnd.on_play(None)

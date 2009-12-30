# debugging hack - add . to path
import os, sys
local_module_dir = os.path.join(os.path.dirname(sys.argv[0]), '..')
if os.path.isdir(local_module_dir):
    sys.path.append(local_module_dir)

import gtk
import gobject
import util
import logging
import gobject

from jamaendo.api import LocalDB, Query, Queries, refresh_dump
from jamaui.player import Player, Playlist

gobject.threads_init()

log = logging.getLogger(__name__)

try:
    import hildon
except:
    if util.platform == 'maemo':
        log.critical('Using GTK widgets, install "python2.5-hildon" '
            'for this to work properly.')
    else:
        log.critical('This ui only works in maemo')
        sys.exit(1)

class RefreshDialog(object):
    def __init__(self):
        self.notebook = gtk.Notebook()
        info = gtk.VBox()
        info.pack_start(gtk.Label("Downloading complete DB from jamendo.com."), True, False)
        info.pack_start(gtk.Label("This will download approximately 8 MB."), True, False)
        self.force = hildon.GtkToggleButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        self.force.set_label("Force refresh")

        info.pack_start(self.force, True, False)
        self.notebook.append_page(info)

        pcont = gtk.VBox()
        self.progress = gtk.ProgressBar()
        pcont.pack_start(self.progress, True, False)
        self.notebook.append_page(pcont,
                                  gtk.Label("Updating Database"))
        self.progress.set_fraction(0)
        self.progress.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
        self.progress.set_text("Downloading...")

        self.notebook.append_page(gtk.Label("Database refreshed."))

        self.dialog = hildon.WizardDialog(None, "Refresh", self.notebook)
        self.notebook.connect("switch-page", self.on_switch)
        self.dialog.set_forward_page_func(self.forward_func)

        self.refresher = None

    def on_complete(self, status):
        hildon.hildon_gtk_window_set_progress_indicator(self.dialog, 0)
        if status:
            self.progress.set_fraction(1)
            self.progress.set_text("DB up to date.")
        else:
            self.progress.set_fraction(0)
            self.progress.set_text("Download failed.")

    def on_progress(self, percent):
        if percent < 100:
            self.progress.set_text("Downloading...")
        self.progress.set_fraction(percent/100.0)

    def on_switch(self, notebook, page, num):
        if num == 1:
            hildon.hildon_gtk_window_set_progress_indicator(self.dialog, 1)
            refresh_dump(self.on_complete, self.on_progress, force=self.force.get_active())
        elif self.refresher:
            # cancel download
            pass
        return True

    def forward_func(self, notebook, current, userdata):
        #page = notebook.get_nth_page(current)
        if current == 0:
            return True
        else:
            return False

    def show_all(self):
        self.dialog.show_all()

    def run(self):
        self.dialog.run()

    def hide(self):
        self.dialog.hide()

class PlayerWindow(hildon.StackableWindow):
    def __init__(self, playlist=None):
        hildon.StackableWindow.__init__(self)
        self.set_title("jamaendo")

        self.playlist = Playlist(playlist)
        self.player = Player()
        #self.player.play(playlist)

        vbox = gtk.VBox()

        hbox = gtk.HBox()

        cover = gtk.Image()

        vbox2 = gtk.VBox()

        playlist_pos = gtk.Label("0/0 songs")
        track = gtk.Label("Track name")
        progress = hildon.GtkHScale()
        artist = gtk.Label("Artist")
        album = gtk.Label("Album")

        vbox2.pack_start(playlist_pos, False)
        vbox2.pack_start(track, False)
        vbox2.pack_start(progress, True, True)
        vbox2.pack_start(artist, False)
        vbox2.pack_start(album, False)

        hbox.pack_start(cover, True, True, 0)
        hbox.pack_start(vbox2, True, True, 0)

        vbox.pack_start(hbox, True, True, 0)

        btns = gtk.HButtonBox()
        btns.set_property('layout-style', gtk.BUTTONBOX_SPREAD)

        vbox.pack_end(btns, False, True, 0)

        self.add_stock_button(btns, gtk.STOCK_MEDIA_PREVIOUS, self.on_prev)
        self.add_stock_button(btns, gtk.STOCK_MEDIA_PLAY, self.on_play)
        self.add_stock_button(btns, gtk.STOCK_MEDIA_PAUSE, self.on_pause)
        self.add_stock_button(btns, gtk.STOCK_MEDIA_STOP, self.on_stop)
        self.add_stock_button(btns, gtk.STOCK_MEDIA_NEXT, self.on_next)

        self.add(vbox)

    def add_stock_button(self, btns, stock, cb):
        btn = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_SMALL_TOOLBAR))
        btn.connect('clicked', cb)
        btns.add(btn)

    def on_play(self, button):
        self.player.play(self.playlist)
    def on_pause(self, button):
        self.player.pause()
    def on_prev(self, button):
        self.player.prev()
    def on_next(self, button):
        self.player.next()
    def on_stop(self, button):
        self.player.stop()

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

        self.results = hildon.TouchSelector(text=True)
        self.results.connect("changed", self.selection_changed)

        vbox.pack_start(hbox, False)
        vbox.pack_start(self.results, True, True, 0)

        self.add(vbox)

        self.idmap = {}

        self.pwnd = None

    def on_search(self, w):
        txt = self.entry.get_text()
        print "Search for: %s" % (txt)
        db = LocalDB()
        db.connect()
        for album in db.search_albums(txt):
            title = "%s - %s" % (album['artist'], album['name'])
            self.idmap[title] = album
            print "Found %s" % (album)
            self.results.append_text(title)

    def selection_changed(self, results, userdata):
        current_selection = results.get_current_text()

        album = self.idmap[current_selection]
        selected = [album['id']]
        print "Selected: %s" % (selected)
        album = None
        db = LocalDB()
        db.connect()
        for a in db.get_albums(selected):
            album = a
            break

        if album:
            tracks = album['tracks']
            print "Playing: %s" % (tracks)
            self.pwnd = PlayerWindow(tracks)
            self.pwnd.show_all()

class PlaylistsWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Playlists")

        label = gtk.Label("playlists")
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(label, True, True, 0)
        self.add(vbox)

class FavoritesWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Favorites")

        label = gtk.Label("favorites")
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(label, True, True, 0)
        self.add(vbox)

class Jamaui(object):
    _BG = 'bg.png' # /opt/jamaendo/data/bg.png

    def __init__(self):
        self.app = None
        self.menu = None
        self.window = None

    def create_window(self):
        self.app = hildon.Program()
        self.window = hildon.StackableWindow()
        self.app.add_window(self.window)

        self.window.set_title("jamaendo")
        self.window.connect("destroy", self.destroy)

    def create_menu(self):
        self.menu = hildon.AppMenu()

        #search = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        #search.set_label("Search")
        #search.connect("clicked", self.on_search)
        #self.menu.append(search)

        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Open player")
        player.connect("clicked", self.on_player)
        self.menu.append(player)

        refresh = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        refresh.set_label("Refresh")
        refresh.connect("clicked", self.on_refresh)
        self.menu.append(refresh)

        menu_about = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        menu_about.set_label("About")
        menu_about.connect("clicked", self.show_about, self.window)
        self.menu.append(menu_about)
        gtk.about_dialog_set_url_hook(self.open_link, None)

        self.menu.show_all()
        self.window.set_app_menu(self.menu)

    def find_resource(self, name):
        if os.path.isfile(os.path.join('data', name)):
            return os.path.join('data', name)
        elif os.path.isfile(os.path.join('/opt/jaemendo', name)):
            return os.path.join('/opt/jaemendo', name)
        elif os.path.isfile(os.path.join('/usr/share/jaemendo', name)):
            return os.path.join('/usr/share/jaemendo', name)
        else:
            return name

    def setup_widgets(self):
        background, mask = gtk.gdk.pixbuf_new_from_file(self.find_resource(self._BG)).render_pixmap_and_mask()
        self.window.realize()
        self.window.window.set_back_pixmap(background, False)

        bbox = gtk.HButtonBox()
        alignment = gtk.Alignment(xalign=0.0, yalign=0.8, xscale=1.0)
        alignment.add(bbox)
        bbox.set_property('layout-style', gtk.BUTTONBOX_SPREAD)
        self.bbox = bbox
        self.window.add(alignment)

        self.add_mainscreen_button("Search", "Search for artists/albums", self.on_search)
        self.add_mainscreen_button("Playlists", "Browse playlists", self.on_playlists)
        self.add_mainscreen_button("Favorites", "Your favorite albums", self.on_favorites)

        self.window.show_all()

    def add_mainscreen_button(self, title, subtitle, callback):
        btn = hildon.Button(gtk.HILDON_SIZE_THUMB_HEIGHT,
                            hildon.BUTTON_ARRANGEMENT_VERTICAL)
        btn.set_text(title, subtitle)
        btn.set_property('width-request', 225)
        btn.connect('clicked', callback)
        self.bbox.add(btn)

    def destroy(self, widget):
        gtk.main_quit()

    def show_about(self, w, win):
        dialog = gtk.AboutDialog()
        dialog.set_website("http://github.com/krig")
        dialog.set_website_label("http://github.com/krig")
        dialog.set_name("Jamaendo")
        dialog.set_authors(("Kristoffer Gronlund (Purple Scout AB)",))
        dialog.set_comments("Media player for jamendo.com")
        dialog.set_version('')
        dialog.run()
        dialog.destroy()

    def open_link(self, d, url, data):
        import webbrowser
        webbrowser.open_new(url)


    def on_refresh(self, button):
        dialog = RefreshDialog()
        dialog.show_all()
        dialog.run()
        dialog.hide()

    def on_search(self, button):
        self.searchwnd = SearchWindow()
        self.searchwnd.show_all()

    def on_playlists(self, button):
        self.playlistswnd = PlaylistsWindow()
        self.playlistswnd.show_all()

    def on_favorites(self, button):
        self.favoriteswnd = FavoritesWindow()
        self.favoriteswnd.show_all()

    def on_player(self, button):
        self.playerwnd = PlayerWindow()
        self.playerwnd.show_all()

    '''
    def on_search(self, button):
        if self.searchbar:
            self.searchbar.show()
        else:
            self.searchstore = gtk.ListStore(gobject.TYPE_STRING)
            iter = self.searchstore.append()
            self.searchstore.set(iter, 0, "Test1")
            iter = self.searchstore.append()
            self.searchstore.set(iter, 0, "Test2")
            self.searchbar = hildon.FindToolbar("Search", self.searchstore, 0)
            self.searchbar.set_active(0)
            self.window.add_toolbar(self.searchbar)
            self.searchbar.show()
    '''

    def run(self):
        self.create_window()
        self.create_menu()
        self.setup_widgets()
        self.window.show_all()
        gtk.main()

if __name__=="__main__":
    ui = Jamaui()
    ui.run()


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

# we don't use the local DB...
import jamaendo
from jamaui.player import Player, Playlist
from util import jsonprint

import ossohelper

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

from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)

class PlayerWindow(hildon.StackableWindow):
    def __init__(self, playlist=None):
        hildon.StackableWindow.__init__(self)
        self.set_title("jamaendo")

        self.playlist = Playlist(playlist)
        self.player = Player()

        vbox = gtk.VBox()

        hbox = gtk.HBox()

        self.cover = gtk.Image()
        self.cover.set_size_request(160, 160)
        self.cover.set_from_stock(gtk.STOCK_CDROM, gtk.ICON_SIZE_DIALOG)

        vbox2 = gtk.VBox()

        self.playlist_pos = gtk.Label()
        self.track = gtk.Label()
        self.progress = hildon.GtkHScale()
        self.artist = gtk.Label()
        self.album = gtk.Label()

        self.set_labels('track name', 'artist', 'album', 0, 0)

        vbox2.pack_start(self.playlist_pos, False)
        vbox2.pack_start(self.track, False)
        vbox2.pack_start(self.progress, True, True)
        vbox2.pack_start(self.artist, False)
        vbox2.pack_start(self.album, False)

        hbox.pack_start(self.cover, True, True, 0)
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

    def set_labels(self, track, artist, album, playlist_pos, playlist_size):
        self.playlist_pos.set_markup('<span size="small">%s/%s songs</span>'%(playlist_pos, playlist_size))
        self.track.set_markup('<span size="large">%s</span>'%(track))
        self.artist.set_markup(artist)
        self.album.set_markup('<span foreground="#cccccc">%s</span>'%(album))

    def update_state(self):
        item = self.playlist.current()
        if item:
            if not item.name:
                item.load()
            print "current:", item
            self.set_labels(item.name, item.artist_name, item.album_name,
                            self.playlist.current_index(), len(self.playlist))
            self.cover.set_from_file(jamaendo.get_album_cover(item.album_id, size=160))

    def on_play(self, button):
        self.player.play(self.playlist)
        self.update_state()
    def on_pause(self, button):
        self.player.pause()
    def on_prev(self, button):
        self.player.prev()
        self.update_state()
    def on_next(self, button):
        self.player.next()
        self.update_state()
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
            self.pwnd = PlayerWindow(tracks)
            self.pwnd.show_all()

class RadiosWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Radios")

        label = gtk.Label("Radios")
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(label, True, True, 0)
        self.add(vbox)

class FeaturedWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Featured")

        label = gtk.Label("featured")
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(label, True, True, 0)
        self.add(vbox)

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

        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Favorites")
        player.connect("clicked", self.on_favorites)
        self.menu.append(player)

        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Playlists")
        player.connect("clicked", self.on_playlists)
        self.menu.append(player)

        # Don't use localdb ATM
        #refresh = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        #refresh.set_label("Refresh")
        #refresh.connect("clicked", self.on_refresh)
        #self.menu.append(refresh)

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
            return None

    def setup_widgets(self):
        bgimg = self.find_resource(self._BG)
        if bgimg:
            background, mask = gtk.gdk.pixbuf_new_from_file(bgimg).render_pixmap_and_mask()
            self.window.realize()
            self.window.window.set_back_pixmap(background, False)

        bbox = gtk.HButtonBox()
        alignment = gtk.Alignment(xalign=0.0, yalign=0.8, xscale=1.0)
        alignment.add(bbox)
        bbox.set_property('layout-style', gtk.BUTTONBOX_SPREAD)
        self.bbox = bbox
        self.window.add(alignment)

        self.add_mainscreen_button("Featured", "Most listened to", self.on_featured)
        self.add_mainscreen_button("Radios", "The best in free music", self.on_radios)
        self.add_mainscreen_button("Search", "Search for artists/albums", self.on_search)

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
        dialog.set_authors(("Kristoffer Gronlund (Purple Scout AB)",))
        dialog.set_comments("""Jamaendo plays music from the music catalog of JAMENDO.

JAMENDO is an online platform that distributes musical works under Creative Commons licenses.""")
        dialog.set_version('')
        dialog.run()
        dialog.destroy()

    def open_link(self, d, url, data):
        import webbrowser
        webbrowser.open_new(url)


    #def on_refresh(self, button):
    #    dialog = RefreshDialog()
    #    dialog.show_all()
    #    dialog.run()
    #    dialog.hide()

    def on_featured(self, button):
        self.featuredwnd = FeaturedWindow()
        self.featuredwnd.show_all()

    def on_radios(self, button):
        self.radiownd = RadioWindow()
        self.radiownd.show_all()

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
        ossohelper.application_init('org.jamaendo', '0.1')
        self.create_window()
        self.create_menu()
        self.setup_widgets()
        self.window.show_all()
        gtk.main()
        ossohelper.application_exit()

if __name__=="__main__":
    ui = Jamaui()
    ui.run()


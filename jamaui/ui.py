import os, sys
import gtk
import gobject
import util
import logging
from settings import settings

import ossohelper

gobject.threads_init()

log = logging.getLogger(__name__)

VERSION = '1'

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

import jamaendo

from playerwindow import open_playerwindow
from search import SearchWindow
from featured import FeaturedWindow
from radios import RadiosWindow
from favorites import FavoritesWindow

class PlaylistsWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Playlists")

        label = gtk.Label("Playlists")
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(label, True, True, 0)
        self.add(vbox)

class Jamaui(object):
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

        self.CONFDIR = os.path.expanduser('~/MyDocs/.jamaendo')
        jamaendo.set_cache_dir(self.CONFDIR)
        settings.set_filename(os.path.join(self.CONFDIR, 'ui_settings'))
        settings.load()

    def save_settings(self):
        settings.save()

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

        #player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        #player.set_label("Playlists")
        #player.connect("clicked", self.on_playlists)
        #self.menu.append(player)

        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Settings")
        player.connect("clicked", self.on_settings)
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


    def setup_widgets(self):
        bgimg = util.find_resource('bg.png')
        if bgimg:
            background, mask = gtk.gdk.pixbuf_new_from_file(bgimg).render_pixmap_and_mask()
            self.window.realize()
            self.window.window.set_back_pixmap(background, False)

        bbox = gtk.HButtonBox()
        alignment = gtk.Alignment(xalign=0.2, yalign=0.925, xscale=1.0)
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

    #def add_featured_button(self):
    #    self.featured_sel = hildon.TouchSelector(text=True)
    #    self.featured_sel.append_text("Albums of the week")
    #    self.featured_sel.append_text("Tracks of the week")
    #    self.featured_sel.append_text("New releases")
    #    btn = hildon.PickerButton(gtk.HILDON_SIZE_THUMB_HEIGHT,
    #                              hildon.BUTTON_ARRANGEMENT_VERTICAL)
    #    btn.set_text("Featured", "Most listened to")
    #    btn.set_property('width-request', 225)
    #    btn.set_selector(self.featured_sel)
    #    self.featured_btn = btn
    #    self.bbox.add(btn)

    def destroy(self, widget):
        gtk.main_quit()

    def show_about(self, w, win):
        dialog = gtk.AboutDialog()
        dialog.set_program_name("jamaendo")
        dialog.set_website("http://github.com/krig")
        dialog.set_website_label("http://github.com/krig")
        dialog.set_version(VERSION)
        dialog.set_authors(("Kristoffer Gronlund <kristoffer.gronlund@purplescout.se>",))
        dialog.set_comments("""Jamaendo plays music from the music catalog of JAMENDO.

JAMENDO is an online platform that distributes musical works under Creative Commons licenses.""")
        gtk.about_dialog_set_email_hook(self.open_link, dialog)
        gtk.about_dialog_set_url_hook(self.open_link, dialog)
        dialog.connect( 'response', lambda dlg, response: dlg.destroy())
        for parent in dialog.vbox.get_children():
            for child in parent.get_children():
                if isinstance(child, gtk.Label):
                    child.set_selectable(False)
                    child.set_alignment(0.0, 0.5)
        dialog.run()
        dialog.destroy()

    def open_link(self, d, url, data):
        print "url: %s" % (url)
        import webbrowser
        webbrowser.open_new(url)


    #def on_refresh(self, button):
    #    dialog = RefreshDialog()
    #    dialog.show_all()
    #    dialog.run()
    #    dialog.hide()

    def on_featured(self, button):
        dialog = hildon.PickerDialog(self.window)
        sel = hildon.TouchSelector(text=True)
        for feature, _ in FeaturedWindow.features:
            sel.append_text(feature)
        dialog.set_selector(sel)
        dialog.set_title("Featured")
        if dialog.run() == gtk.RESPONSE_OK:
            txt = sel.get_current_text()
            self.featuredwnd = FeaturedWindow(txt)
            self.featuredwnd.show_all()
        dialog.destroy()

    def on_radios(self, button):
        self.radioswnd = RadiosWindow()
        self.radioswnd.show_all()

    def on_search(self, button):
        self.searchwnd = SearchWindow()
        self.searchwnd.show_all()

    def on_playlists(self, button):
        self.playlistswnd = PlaylistsWindow()
        self.playlistswnd.show_all()

    def on_settings(self, button):
        dialog = gtk.Dialog()
        dialog.set_title("Settings")
        dialog.add_button( gtk.STOCK_OK, gtk.RESPONSE_OK )
        vbox = dialog.vbox
        tbl = gtk.Table(1, 2)
        tbl.attach(gtk.Label("Username:"), 0, 1, 0, 1)
        entry = hildon.Entry(gtk.HILDON_SIZE_FINGER_HEIGHT)
        entry.set_placeholder("jamendo.com username")
        if settings.user:
            entry.set_text(settings.user)
        tbl.attach(entry, 1, 2, 0, 1)
        vbox.pack_start(tbl, True, True, 2)
        dialog.show_all()
        result = dialog.run()
        val = entry.get_text()
        dialog.destroy()
        print val, result
        if val and result == gtk.RESPONSE_OK:
            print "new user name:", val
            settings.user = val
            self.save_settings()


    def on_favorites(self, button):
        self.favoriteswnd = FavoritesWindow()
        self.favoriteswnd.show_all()

    def on_player(self, button):
        open_playerwindow([])

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


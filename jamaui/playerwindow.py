import gtk
import hildon
import jamaendo
from player import Playlist, the_player

class PlayerWindow(hildon.StackableWindow):
    def __init__(self, playlist=None):
        hildon.StackableWindow.__init__(self)
        self.set_title("jamaendo")

        self.connect('hide', self.on_hide)
        self.connect('destroy', self.on_destroy)

        self.playlist = Playlist(playlist)
        self.player = the_player

        vbox = gtk.VBox()

        hbox = gtk.HBox()

        self.cover = gtk.Image()
        self.cover.set_size_request(200, 200)
        self.cover.set_from_stock(gtk.STOCK_CDROM, gtk.ICON_SIZE_DIALOG)

        vbox2 = gtk.VBox()

        self.playlist_pos = gtk.Label()
        self.track = gtk.Label()
        self.progress = hildon.GtkHScale()
        self.artist = gtk.Label()
        self.album = gtk.Label()

        if self.player.playlist.current_index() > -1:
            pl = self.player.playlist
            track = pl.current()
            self.set_labels(track.name, track.artist_name, track.album_name, pl.current_index(), pl.size())
        else:
            self.set_labels('track name', 'artist', 'album', 0, 0)

        vbox2.pack_start(self.track, True)
        vbox2.pack_start(self.artist, False)
        vbox2.pack_start(self.album, False)
        vbox2.pack_start(self.playlist_pos, False)
        vbox2.pack_start(self.progress, False)

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

        print "Created player window, playlist: %s" % (self.playlist)

    def on_hide(self, wnd):
        print "Hiding player window"

    def on_destroy(self, wnd):
        print "Destroying player window"
        if self.player:
            self.player.stop()

    def add_stock_button(self, btns, stock, cb):
        btn = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_SMALL_TOOLBAR))
        btn.connect('clicked', cb)
        btns.add(btn)

    def set_labels(self, track, artist, album, playlist_pos, playlist_size):
        self.playlist_pos.set_markup('<span size="small">%s/%s songs</span>'%(playlist_pos, playlist_size))
        self.track.set_markup('<span size="x-large">%s</span>'%(track))
        self.artist.set_markup('<span size="large">%s</span>'%(artist))
        self.album.set_markup('<span foreground="#aaaaaa">%s</span>'%(album))

    def update_state(self):
        item = self.playlist.current()
        if item:
            if not item.name:
                item.load()
            print "current:", item
            self.set_labels(item.name, item.artist_name, item.album_name,
                            self.playlist.current_index(), self.playlist.size())
            coverfile = jamaendo.get_album_cover(int(item.album_id), size=200)
            print "coverfile:", coverfile
            self.cover.set_from_file(coverfile)

    def play_tracks(self, tracks):
        self.playlist = Playlist(tracks)
        self.player.play(self.playlist)
        self.update_state()

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

def open_playerwindow(tracks):
    player = PlayerWindow(tracks)
    player.show_all()
    return player

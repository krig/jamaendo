import gtk
import hildon
import jamaendo
from playerwindow import open_playerwindow
from settings import settings
import util

class ShowAlbum(hildon.StackableWindow):
    def __init__(self, album):
        hildon.StackableWindow.__init__(self)
        self.set_title("Album")
        self.album = album

        top_vbox = gtk.VBox()
        top_hbox = gtk.HBox()
        vbox1 = gtk.VBox()
        self.cover = gtk.Image()
        self.bbox = gtk.HButtonBox()
        self.bbox.set_property('layout-style', gtk.BUTTONBOX_SPREAD)
        self.goto_artist = self.make_imagebutton('artist', self.on_goto_artist)
        self.download = self.make_imagebutton('download', self.on_download)
        self.favorite = self.make_imagebutton('favorite', self.on_favorite)
        self.license = self.make_imagebutton('license', self.on_license)
        self.playbtn = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        self.playbtn.set_label("Play album")
        self.playbtn.set_border_width(0)
        self.playbtn.connect('clicked', self.on_play)

        vbox2 = gtk.VBox()
        self.albumtitle = gtk.Label()
        self.albumtitle.set_markup('<big>%s</big>' % (album.name))
        self.artist = gtk.Label()
        self.artist.set_markup('<span color="#cccccc">%s</span>'%(album.artist_name))
        self.trackarea = hildon.PannableArea()

        self.album_store = gtk.ListStore(int, str, int)
        self.album_view = gtk.TreeView(self.album_store)
        col0 = gtk.TreeViewColumn('Num')
        col = gtk.TreeViewColumn('Name')
        self.album_view.append_column(col0)
        self.album_view.append_column(col)
        cell0 = gtk.CellRendererText()
        col0.pack_start(cell0, True)
        col0.add_attribute(cell0, 'text', 0)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', 1)
        self.album_view.set_search_column(1)
        col.set_sort_column_id(0)
        self.album_view.connect('row-activated', self.row_activated)

        for track in jamaendo.get_tracks(album.ID):
            self.album_store.append([track.numalbum, track.name, track.ID])

        top_vbox.pack_start(self.albumtitle, False)
        top_vbox.pack_start(top_hbox)
        top_hbox.pack_start(vbox1, False)
        top_hbox.pack_start(vbox2, True)
        vbox1.pack_start(self.cover, True)
        vbox1.pack_start(self.playbtn, False)
        vbox1.pack_start(self.bbox, False)
        self.bbox.add(self.goto_artist)
        self.bbox.add(self.download)
        self.bbox.add(self.favorite)
        self.bbox.add(self.license)
        vbox2.pack_start(self.artist, False)
        vbox2.pack_start(self.trackarea, True)
        self.trackarea.add(self.album_view)

        self.add(top_vbox)

        coverfile = jamaendo.get_album_cover(self.album.ID, size=200)
        self.cover.set_from_file(coverfile)

        self.show_all()

    def make_imagebutton(self, name, cb):
        btn = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        btn.set_relief(gtk.RELIEF_NONE)
        img = util.find_resource('icon_%s.png'%(name))
        if img:
            btn.set_image(gtk.image_new_from_file(img))
        else:
            btn.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_SMALL_TOOLBAR))
        btn.set_border_width(0)
        btn.connect('clicked', cb)
        return btn

    def on_goto_artist(self, btn):
        artist = jamaendo.get_artist(int(self.album.artist_id))
        self.open_item(artist)

    def on_download(self, btn):
        banner = hildon.hildon_banner_show_information(self, '', "Downloads disabled in this version")
        banner.set_timeout(2000)

    def on_favorite(self, btn):
        settings.favorite(self.album)
        banner = hildon.hildon_banner_show_information(self, '', "Favorite added")
        banner.set_timeout(2000)


    def on_license(self, btn):
        url = self.album.license_url
        import webbrowser
        webbrowser.open_new(url)

    def on_play(self, btn):
        self.open_item(self.album)

    def row_activated(self, treeview, path, view_column):
        pass

    def open_item(self, item):
        if isinstance(item, jamaendo.Album):
            tracks = jamaendo.get_tracks(item.ID)
            if tracks:
                wnd = open_playerwindow()
                wnd.play_tracks(tracks)
        elif isinstance(item, jamaendo.Artist):
            from showartist import ShowArtist
            wnd = ShowArtist(item)
            wnd.show_all()
        elif isinstance(item, jamaendo.Track):
            wnd = open_playerwindow()
            wnd.play_tracks([item])

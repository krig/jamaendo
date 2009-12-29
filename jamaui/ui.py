import gtk
import gobject
import util

log = logging.getLogger(__name__)

try:
    import hildon
except:
    if util.platform == 'maemo':
        log.critical( 'Using GTK widgets, install "python2.5-hildon" '
            'for this to work properly.' )

class Jamaui(object):
    def __init__(self):
        self.app = None
        self.window = None
        if util.platform == 'maemo':
            self.app = hildon.Program()
            self.window = hildon.Window()
            self.app.add_window(window)
        else:
            self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

    def run(self):
        self.window.show()
        gtk.main()


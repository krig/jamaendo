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

class Jamaui(object):
    _DATA = 'data/bg.png' # /opt/jamaendo/data/bg.png

    def __init__(self):
        self.app = hildon.Program()
        self.window = hildon.Window()
        self.app.add_window(window)

        self.window.set_title("jamaendo")
        self.window.connect("destroy", gtk.main_quit, None)

        img = gtk.image_new_from_file(self._DATA)
        self.window.add(img)

    def run(self):
        self.window.show_all()
        gtk.main()

if __name__=="__main__":
    ui = Jamaui()
    ui.run()


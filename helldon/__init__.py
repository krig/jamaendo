import gtk

gtk.HILDON_SIZE_AUTO = -1
gtk.HILDON_SIZE_AUTO_WIDTH = -1
gtk.HILDON_SIZE_FINGER_HEIGHT = 32
gtk.HILDON_SIZE_THUMB_HEIGHT = 48

BUTTON_ARRANGEMENT_VERTICAL = 1

def hildon_gtk_window_set_progress_indicator(wnd, onoff):
    pass

class Program(gtk.Window):
    instance = None

    def __init__(self):
        gtk.Window.__init__(self, type=gtk.WINDOW_TOPLEVEL)
        self._vbox = gtk.VBox()
        self._title = gtk.Label("Jamaendo")
        self._backbtn = gtk.Button("<<<")
        self._hbox = gtk.HBox()
        self._hbox.pack_start(self._title, True)
        self._hbox.pack_start(self._backbtn, False)
        self._notebook = gtk.Notebook()
        self._notebook.set_size_request(800, 445)
        self._notebook.set_show_tabs(False)
        self._vbox.pack_start(self._hbox, False)
        self._vbox.pack_start(self._notebook, True)
        self.add(self._vbox)
        self.show_all()
        Program.instance = self

    def add_window(self, wnd):
        pass

    def add_stackable(self, wnd):
        idx = self._notebook.append_page(wnd)
        self._notebook.set_current_page(idx)
        wnd.show_all()
        wnd._nb_index = idx

class StackableWindow(gtk.Frame):
    def __init__(self):
        gtk.Frame.__init__(self)
        self._nb_index = 0
        Program.instance.add_stackable(self)
    def set_app_menu(self, menu):
        pass

    def set_title(self, title):
        Program.instance._title.set_text(title)#_notebook.set_tab_label_text(self, title)

class AppMenu(object):
    def __init__(self):
        pass

    def append(self, widget):
        pass

    def show_all(self):
        pass

class GtkButton(gtk.Button):
    def __init__(self, size):
        gtk.Button.__init__(self)


class Button(gtk.Button):
    def __init__(self, size, layout):
        gtk.Button.__init__(self)

    def set_text(self, title, subtitle):
        self.set_label(title)

class PannableArea(gtk.ScrolledWindow):
    pass

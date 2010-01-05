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
        self._backbtn.connect('clicked', self.on_back)

        self._stack = []

    def add_window(self, wnd):
        pass

    def push_stackable(self, wnd):
        while self._notebook.get_n_pages() > 0:
            p = self._notebook.get_nth_page(0)
            self._stack.append(p)
            self._notebook.remove_page(0)
            p.hide()

        idx = self._notebook.append_page(wnd)
        self._notebook.set_current_page(idx)
        wnd.show_all()
        wnd._nb_index = idx

    def popped_stackable(self, wnd=None):
        pass

    def pop_stackable(self):
        while self._notebook.get_n_pages() > 0:
            p = self._notebook.get_nth_page(0)
            self._notebook.remove_page(0)
            p.hide()
        if len(self._stack):
            tail = self._stack.pop()
            self.push_stackable(tail)

    def on_back(self, *args):
        self.pop_stackable()

class StackableWindow(gtk.Frame):
    def __init__(self):
        gtk.Frame.__init__(self)
        self._nb_index = 0
        Program.instance.push_stackable(self)
        self.connect('destroy', self.on_destroy)
    def set_app_menu(self, menu):
        pass

    def set_title(self, title):
        Program.instance._title.set_text(title)#_notebook.set_tab_label_text(self, title)

    def on_destroy(self, *args):
        Program.instance.popped_stackable(self)

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

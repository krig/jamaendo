import gtk
import cairo

gtk.HILDON_SIZE_AUTO = -1
gtk.HILDON_SIZE_AUTO_WIDTH = -1
gtk.HILDON_SIZE_FINGER_HEIGHT = 32
gtk.HILDON_SIZE_THUMB_HEIGHT = 48

BUTTON_ARRANGEMENT_VERTICAL = 1

def hildon_gtk_window_set_progress_indicator(wnd, onoff):
    pass

def hildon_banner_show_information(wnd, icons, desc):
    class Blah(object):
        def set_timeout(self, t):
            pass
    print "Banner: %s" % (desc)
    return Blah()

def transparent_expose(widget, event):
    bgimg = 'data/bg.png'
    if bgimg:
        background, mask = gtk.gdk.pixbuf_new_from_file(bgimg).render_pixmap_and_mask()
        #self.realize()
        widget.window.set_back_pixmap(background, False)
        #widget.window.clear()
    #cr = widget.window.cairo_create()
    #cr.set_operator(cairo.OPERATOR_CLEAR)
    # Ugly but we don't have event.region
    #region = gtk.gdk.region_rectangle(event.area)
    #cr.region(region)
    #cr.fill()
    return False

class Program(gtk.Window):
    instance = None

    def __init__(self):
        gtk.Window.__init__(self, type=gtk.WINDOW_TOPLEVEL)
        self.set_app_paintable(True)
        self._vbox = gtk.VBox()
        self._title = gtk.Label("Jamaendo")
        self._title.set_alignment(0.1, 0.5)
        self._backbtn = gtk.Button("Quit")
        self._backbtn.set_alignment(1.0, 0.5)
        self._hbox = gtk.HBox()
        self._hbox.pack_start(self._title, True)
        self._hbox.pack_start(self._backbtn, False)
        self._notebook = gtk.Notebook()
        self._notebook.set_size_request(800, 445)
        self._notebook.set_show_tabs(False)
        self._notebook.set_app_paintable(True)
        self._notebook.connect("expose-event", transparent_expose)
        self._vbox.pack_start(self._hbox, False)
        self._vbox.pack_start(self._notebook, True)
        self.add(self._vbox)
        self.show_all()
        Program.instance = self
        self._backbtn.connect('clicked', self.on_back)

        bgimg = 'data/bg.png'
        if bgimg:
            background, mask = gtk.gdk.pixbuf_new_from_file(bgimg).render_pixmap_and_mask()
            self.set_app_paintable(True)
            self.realize()
            self.window.set_back_pixmap(background, False)
            self.window.clear()

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
        if self._stack:
            self._backbtn.set_label("<<<")
        else:
            self._backbtn.set_label("Quit")
        self._notebook.window.clear()

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
        if self._stack:
            self._backbtn.set_label("<<<")
        else:
            self._backbtn.set_label("Quit")
        if self._notebook.get_n_pages() == 0:
            gtk.main_quit()

    def size(self):
        return len(self._stack)+1

    def pop(self, sz):
        ret = [x for x in self._stack] + [self._notebook.get_nth_page(0)]
        while self._stack:
            self.pop_stackable()
        return ret

    def push_list(self, windows):
        for window in windows:
            self.push_stackable(window)

    #        windows = stack.pop(sz)
    #    windows.remove(player)
    #    windows.append(player)
    #    stack.push_list(windows)


class StackableWindow(gtk.EventBox):
    def __init__(self):
        gtk.EventBox.__init__(self)
        self.set_app_paintable(True)
        #self.connect("expose-event", transparent_expose)
        self._nb_index = 0
        Program.instance.push_stackable(self)
        self.connect('destroy', self.on_destroy)
    def set_app_menu(self, menu):
        pass

    def set_title(self, title):
        Program.instance._title.set_text(title)#_notebook.set_tab_label_text(self, title)

    def on_destroy(self, *args):
        Program.instance.popped_stackable(self)

    def get_stack(self):
        return Program.instance

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
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

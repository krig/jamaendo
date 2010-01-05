# what the fuck, GTK
import gtk
try:
    import hildon
    _using_helldon = False
except:
    import helldon as hildon
    _using_helldon = True

class ListBox(gtk.TreeView):
    def __init__(self):
        gtk.TreeView.__init__(self)
        self.store = gtk.ListStore(str)
        column = gtk.TreeViewColumn("Text")
        textRenderer = gtk.CellRendererText()
        column.pack_start(textRenderer, True)
        column.set_attributes(textRenderer, text = 0)
        self.append_column(column)
        self.set_model(self.store)

    def get_text(self, path):
        it = self.store.get_iter(path)
        if not it:
            return None
        ret = self.store.get(it, 0)
        return ret[0]

    def get_selected_text(self):
        model, it = self.get_selection().get_selected()
        if not it:
            return None
        ret = self.store.get(it, 0)
        return ret[0]

    def append(self, text):
        self.store.append([text])

    def on_select(self, callback, *args):
        def cb(lb, path, col):
            ret = self.get_text(path)
            if ret:
                callback(ret, *args)
        self.connect('row-activated', cb)

class ListDialog(gtk.Dialog):
    def __init__(self, title, parent=None):
        gtk.Dialog.__init__(self, title, parent if not _using_helldon else None)
        self.listbox = ListBox()
        panarea = hildon.PannableArea()
        panarea.add(self.listbox)
        panarea.set_size_request(800, 300)
        self.vbox.pack_start(panarea, True, True, 0)

        self.selected = None

        def selector(selected, dialog):
            if selected:
                self.selected = selected
                dialog.response(gtk.RESPONSE_OK)
        self.listbox.on_select(selector, self)

class ButtonListDialog(gtk.Dialog):
    def __init__(self, title, parent=None):
        gtk.Dialog.__init__(self, title, parent if not _using_helldon else None)
        self.panarea = hildon.PannableArea()
        self.panarea.set_size_request(800, 400)
        self.buttons = gtk.VBox(False, 0)
        self.panarea.add_with_viewport(self.buttons)
        self.vbox.pack_start(self.panarea, True, True, 0)

    def add_button(self, label, clickcb, *args):
        btn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH|gtk.HILDON_SIZE_FINGER_HEIGHT, hildon.BUTTON_ARRANGEMENT_VERTICAL)
        btn.set_label(label)
        btn.connect('clicked', clickcb, *args)
        self.buttons.pack_end(btn, False, False, 0)


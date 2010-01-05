#!/usr/bin/env python
#
# This file is part of Jamaendo.
# Copyright (c) 2010 Kristoffer Gronlund
#
# Jamaendo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jamaendo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jamaendo.  If not, see <http://www.gnu.org/licenses/>.
#
# Player code heavily based on http://thpinfo.com/2008/panucci/:
#  A resuming media player for Podcasts and Audiobooks
#  Copyright (c) 2008-05-26 Thomas Perl <thpinfo.com>
#  (based on http://pygstdocs.berlios.de/pygst-tutorial/seeking.html)
#
import gtk
try:
    import hildon
except:
    import helldon as hildon
import jamaendo
from settings import settings
import logging

log = logging.getLogger(__name__)

def _alist(l, match):
    for key, value in l:
        if key == match:
            return value
    return None

def _show_banner(parent, message, timeout = 2000):
    banner = hildon.hildon_banner_show_information(parent, '', message)
    banner.set_timeout(2000)

from listbox import ListDialog

def add_to_playlist(wnd, track):
    if not track:
        _show_banner(wnd, "Nothing to add")
        return

    dialog = ListDialog('Add to playlist', wnd)
    for name,_ in settings.playlists.iteritems():
        dialog.listbox.append(name)
    dialog.listbox.append("New...")
    try:
        dialog.show_all()
        if dialog.run() == gtk.RESPONSE_OK:
            selected_playlist = dialog.selected
            if selected_playlist == "New...":
                dialog.hide()
                selected_playlist = create_new_playlist(wnd)
            if track and selected_playlist:
                if isinstance(track, (list, tuple)):
                    for t in track:
                        settings.add_to_playlist(selected_playlist, {'id':t.ID, 'data':t.get_data()})
                else:
                    settings.add_to_playlist(selected_playlist, {'id':track.ID, 'data':track.get_data()})
                settings.save()
                _show_banner(wnd, "Added to playlist '%s'" % (selected_playlist))
    finally:
        dialog.destroy()

def create_new_playlist(wnd):
    dia_name = gtk.Dialog()
    dia_name.set_title("New playlist")
    dia_name.add_button( gtk.STOCK_OK, gtk.RESPONSE_OK )
    entry = hildon.Entry(gtk.HILDON_SIZE_FINGER_HEIGHT)
    entry.set_placeholder("Enter name")
    entry.set_max_length(32)
    entry.connect('activate', lambda entry, dialog: dialog.response(gtk.RESPONSE_OK), dia_name)
    dia_name.vbox.pack_start(entry, True, True, 0)
    dia_name.show_all()
    if dia_name.run() != gtk.RESPONSE_OK:
        return False
    selected_playlist = entry.get_text()
    dia_name.destroy()
    if selected_playlist == '' or selected_playlist == 'New...':
        return False
    elif settings.get_playlist(selected_playlist):
        _show_banner(wnd, "Playlist '%s' already exists!" % (selected_playlist))
        return False
    return selected_playlist


class PlaylistsWindow(hildon.StackableWindow):
    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_title("Playlists")

        self.panarea = hildon.PannableArea()

        (self.COL_NAME, self.COL_INFO) = range(2)
        self.store = gtk.ListStore(str, str)
        self.treeview = gtk.TreeView()
        self.treeview.set_model(self.store)

        col = gtk.TreeViewColumn('Name')
        self.treeview.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', self.COL_NAME)
        self.treeview.set_search_column(self.COL_NAME)
        col.set_sort_column_id(self.COL_NAME)

        col = gtk.TreeViewColumn('Info')
        self.treeview.append_column(col)
        cell = gtk.CellRendererText()
        cell.set_property('xalign', 1.0)
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', self.COL_INFO)

        self.treeview.connect('row-activated', self.row_activated)

        self.panarea.add(self.treeview)

        self.add(self.panarea)

        def trackcount(lst):
            ln = len(lst)
            if ln > 1:
                return "(%d tracks)"%(ln)
            elif ln == 1:
                return "(1 track)"
            return "(empty)"

        for key, lst in sorted(list(settings.playlists.iteritems())):
            self.store.append([key, trackcount(lst)])

    def row_activated(self, treeview, path, view_column):
        name = self.store.get(self.store.get_iter(path), self.COL_NAME)[0]
        pl = settings.get_playlist(name)
        if pl:
            from playerwindow import open_playerwindow
            wnd = open_playerwindow()
            wnd.play_tracks(pl)

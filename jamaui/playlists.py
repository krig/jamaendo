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
from albumlist import PlaylistList

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
        self.playlistlist = PlaylistList()
        self.playlistlist.empty_message = "No playlists"
        self.playlistlist.connect('row-activated', self.row_activated)
        self.panarea.add(self.playlistlist)
        self.add(self.panarea)

        for key, lst in sorted(list(settings.playlists.iteritems())):
            self.playlistlist.add_playlist(key, lst)
        self.playlistlist.set_loading(False)

        self.create_menu()

    def create_menu(self):
        def on_player(*args):
            from playerwindow import open_playerwindow
            open_playerwindow()
        self.menu = hildon.AppMenu()
        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Open player")
        player.connect("clicked", on_player)
        self.menu.append(player)
        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Delete playlists")
        player.connect("clicked", self.on_delete_playlists)
        self.menu.append(player)
        self.menu.show_all()
        self.set_app_menu(self.menu)

    def on_delete_playlists(self, *args):
        _show_banner(self, "TODOO")

    def row_activated(self, treeview, path, view_column):
        sel = self.playlistlist.get_playlist_name(path)
        pl = settings.get_playlist(sel)
        if pl:
            from playerwindow import open_playerwindow
            wnd = open_playerwindow()
            wnd.play_tracks(pl)

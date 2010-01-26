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
# Jamaendo jamendo.com API wrapper licensed under the New BSD License;
# see module for details.
#

import os, sys
import gtk
import gobject
import util
import logging
from settings import settings

import ossohelper

gobject.threads_init()

log = logging.getLogger(__name__)

VERSION = '0.2.5'

try:
    import hildon
except:
    if util.platform == 'maemo':
        log.critical('Using GTK widgets, install "python2.5-hildon" '
            'for this to work properly.')
    else:
        log.critical('This ui (probably) only works in maemo')
        import helldon as hildon

from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)

import jamaendo

from postoffice import postoffice
from playerwindow import open_playerwindow
from search import SearchWindow
from featured import FeaturedWindow
from radios import RadiosWindow
from favorites import FavoritesWindow
from playlists import PlaylistsWindow
from listbox import ButtonListDialog

class Jamaui(object):
    def __init__(self):
        self.app = None
        self.menu = None
        self.window = None

    def create_window(self):
        log.debug("Creating main window...")
        self.app = hildon.Program()
        self.window = hildon.StackableWindow()
        self.app.add_window(self.window)

        self.window.set_title("jamaendo")

        self.window.connect("destroy", self.destroy)

        self.CONFDIR = os.path.expanduser('~/MyDocs/.jamaendo')
        jamaendo.set_cache_dir(self.CONFDIR)
        settings.set_filename(os.path.join(self.CONFDIR, 'ui_settings'))
        settings.load()

        postoffice.connect('request-album-cover', self, self.on_request_cover)
        postoffice.connect('request-images', self, self.on_request_images)
        log.debug("Created main window.")

    def create_menu(self):
        self.menu = hildon.AppMenu()

        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Open player")
        player.connect("clicked", self.on_player)
        self.menu.append(player)

        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Favorites")
        player.connect("clicked", self.on_favorites)
        self.menu.append(player)

        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Playlists")
        player.connect("clicked", self.on_playlists)
        self.menu.append(player)

        player = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        player.set_label("Settings")
        player.connect("clicked", self.on_settings)
        self.menu.append(player)

        menu_about = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        menu_about.set_label("About")
        menu_about.connect("clicked", self.show_about, self.window)
        self.menu.append(menu_about)
        gtk.about_dialog_set_url_hook(self.open_link, None)

        self.menu.show_all()
        self.window.set_app_menu(self.menu)


    def setup_widgets(self):
        bgimg = util.find_resource('bg.png')
        if bgimg:
            background, mask = gtk.gdk.pixbuf_new_from_file(bgimg).render_pixmap_and_mask()
            self.window.realize()
            self.window.window.set_back_pixmap(background, False)

        bbox = gtk.HButtonBox()
        alignment = gtk.Alignment(xalign=0.2, yalign=0.4, xscale=1.0)
        alignment.add(bbox)
        bbox.set_property('layout-style', gtk.BUTTONBOX_SPREAD)
        self.bbox = bbox
        self.window.add(alignment)

        self.add_mainscreen_button("Featured", "Most listened to", self.on_featured)
        self.add_mainscreen_button("Radios", "The best in free music", self.on_radios)
        self.add_mainscreen_button("Search", "Search for artists/albums", self.on_search)

        self.window.show_all()

    def add_mainscreen_button(self, title, subtitle, callback):
        btn = hildon.Button(gtk.HILDON_SIZE_THUMB_HEIGHT,
                            hildon.BUTTON_ARRANGEMENT_VERTICAL)
        btn.set_text(title, subtitle)
        btn.set_property('width-request', 225)
        btn.connect('clicked', callback)
        self.bbox.add(btn)

    def on_request_cover(self, albumid, size):
        jamaendo.get_album_cover_async(self.got_album_cover, int(albumid), size)

    def on_request_images(self, urls):
        jamaendo.get_images_async(self.got_images, urls)

    def got_album_cover(self, albumid, size, cover):
        gtk.gdk.threads_enter()
        postoffice.notify('album-cover', albumid, size, cover)
        gtk.gdk.threads_leave()

    def got_images(self, images):
        gtk.gdk.threads_enter()
        postoffice.notify('images', images)
        gtk.gdk.threads_leave()

    def destroy(self, widget):
        postoffice.disconnect(['request-album-cover', 'request-images'], self)
        settings.save()
        from player import the_player
        if the_player:
            the_player.stop()
        gtk.main_quit()

    def show_about(self, w, win):
        dialog = gtk.AboutDialog()
        dialog.set_program_name("jamaendo")
        dialog.set_website("http://jamaendo.garage.maemo.org/")
        dialog.set_website_label("http://jamaendo.garage.maemo.org/")
        dialog.set_version(VERSION)
        dialog.set_license("""Copyright (c) 2010, Kristoffer Gronlund
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.



 Copyright (c) 2010, Kristoffer Gronlund
 All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:
     * Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
 DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.



 Copyright (c) 2008-2010 The Panucci Audiobook and Podcast Player Project

 Panucci is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Panucci is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Panucci.  If not, see <http://www.gnu.org/licenses/>.

""")
        dialog.set_authors(("Kristoffer Gronlund <kristoffer.gronlund@purplescout.se>",
                            "Based on Panucci, written by Thomas Perl <thpinfo.com>",
                            "Icons by Joseph Wain <http://glyphish.com/>"))
        dialog.set_comments("""Jamaendo plays music from the music catalog of JAMENDO.

JAMENDO is an online platform that distributes musical works under Creative Commons licenses.""")
        gtk.about_dialog_set_email_hook(self.open_link, dialog)
        gtk.about_dialog_set_url_hook(self.open_link, dialog)
        dialog.connect( 'response', lambda dlg, response: dlg.destroy())
        for parent in dialog.vbox.get_children():
            for child in parent.get_children():
                if isinstance(child, gtk.Label):
                    child.set_selectable(False)
                    child.set_alignment(0.0, 0.5)
        dialog.run()
        dialog.destroy()

    def open_link(self, d, url, data):
        import webbrowser
        webbrowser.open_new(url)

    def on_featured(self, button):
        dialog = ButtonListDialog('Featured', self.window)
        def fn(btn, feature):
            self.featuredwnd = FeaturedWindow(feature)
            self.featuredwnd.show_all()
            dialog.response(gtk.RESPONSE_OK)
        for feature, _ in FeaturedWindow.features:
            dialog.add_button(feature, fn, feature)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def on_radios(self, button):
        self.radioswnd = RadiosWindow()
        self.radioswnd.show_all()

    def on_search(self, button):
        self.searchwnd = SearchWindow()
        self.searchwnd.show_all()

    def on_playlists(self, button):
        self.playlistswnd = PlaylistsWindow()
        self.playlistswnd.show_all()

    def on_settings(self, button):
        dialog = gtk.Dialog()
        dialog.set_title("Settings")
        dialog.add_button( gtk.STOCK_OK, gtk.RESPONSE_OK )
        vbox = dialog.vbox
        hboxinner = gtk.HBox()
        hboxinner.pack_start(gtk.Label("Username:"), False, False, 0)
        entry = hildon.Entry(gtk.HILDON_SIZE_FINGER_HEIGHT)
        entry.set_placeholder("jamendo.com username")
        if settings.user:
            entry.set_text(settings.user)
        hboxinner.pack_start(entry, True, True, 0)
        vbox.pack_start(hboxinner, True, True, 0)
        dialog.show_all()
        result = dialog.run()
        val = entry.get_text()
        dialog.destroy()
        if val and result == gtk.RESPONSE_OK:
            settings.user = val
            settings.save()


    def on_favorites(self, button):
        self.favoriteswnd = FavoritesWindow()
        self.favoriteswnd.show_all()

    def on_player(self, button):
        open_playerwindow()

    def run(self):
        ossohelper.application_init('org.jamaendo', '0.1')
        self.create_window()
        self.create_menu()
        self.setup_widgets()
        self.window.show_all()
        gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()
        ossohelper.application_exit()

if __name__=="__main__":
    ui = Jamaui()
    ui.run()


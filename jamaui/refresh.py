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

class RefreshDialog(object):
    def __init__(self):
        self.notebook = gtk.Notebook()
        info = gtk.VBox()
        info.pack_start(gtk.Label("Downloading complete DB from jamendo.com."), True, False)
        info.pack_start(gtk.Label("This will download approximately 8 MB."), True, False)
        self.force = hildon.GtkToggleButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        self.force.set_label("Force refresh")

        info.pack_start(self.force, True, False)
        self.notebook.append_page(info)

        pcont = gtk.VBox()
        self.progress = gtk.ProgressBar()
        pcont.pack_start(self.progress, True, False)
        self.notebook.append_page(pcont,
                                  gtk.Label("Updating Database"))
        self.progress.set_fraction(0)
        self.progress.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
        self.progress.set_text("Downloading...")

        self.notebook.append_page(gtk.Label("Database refreshed."))

        self.dialog = hildon.WizardDialog(None, "Refresh", self.notebook)
        self.notebook.connect("switch-page", self.on_switch)
        self.dialog.set_forward_page_func(self.forward_func)

        self.refresher = None

    def on_complete(self, status):
        hildon.hildon_gtk_window_set_progress_indicator(self.dialog, 0)
        if status:
            self.progress.set_fraction(1)
            self.progress.set_text("DB up to date.")
        else:
            self.progress.set_fraction(0)
            self.progress.set_text("Download failed.")

    def on_progress(self, percent):
        if percent < 100:
            self.progress.set_text("Downloading...")
        self.progress.set_fraction(percent/100.0)

    def on_switch(self, notebook, page, num):
        if num == 1:
            hildon.hildon_gtk_window_set_progress_indicator(self.dialog, 1)
            refresh_dump(self.on_complete, self.on_progress, force=self.force.get_active())
        elif self.refresher:
            # cancel download
            pass
        return True

    def forward_func(self, notebook, current, userdata):
        #page = notebook.get_nth_page(current)
        if current == 0:
            return True
        else:
            return False

    def show_all(self):
        self.dialog.show_all()

    def run(self):
        self.dialog.run()

    def hide(self):
        self.dialog.hide()

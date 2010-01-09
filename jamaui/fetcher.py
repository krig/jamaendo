# Background fetcher:
# Takes a generator and a notification identifier as parameter,
# starts a thread, and post a notification whenever data arrives.
# Posts a completion notification when done.
# Terminates if generator fails or encounters an error.

import threading
from postoffice import postoffice
import jamaendo
import logging

import gobject
import gtk
import hildon

log = logging.getLogger(__name__)

class _Worker(threading.Thread):
    def __init__(self, generator, owner):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.generator = generator
        self.owner = owner

    def _post(self, item):
        def idle_fetch(owner, item):
            postoffice.notify("fetch", owner, item)
        gobject.idle_add(idle_fetch, self.owner, item)

    def _post_ok(self):
        def idle_fetch_ok(owner):
            postoffice.notify("fetch-ok", owner)
        gobject.idle_add(idle_fetch_ok, self.owner)

    def _post_fail(self, e):
        def idle_fetch_fail(owner, e):
            postoffice.notify("fetch-fail", owner, e)
        gobject.idle_add(idle_fetch_fail, self.owner, e)

    def run(self):
        try:
            for item in self.generator():
                self._post(item)
            self._post_ok()
        except jamaendo.JamendoAPIException, e:
            log.exception("Failed to fetch, id %s" % (self.owner))
            self._post_fail(e)

class Fetcher(object):
    def __init__(self, generator, owner, on_item = None, on_ok = None, on_fail = None):
        self.generator = generator
        self.owner = owner
        self.worker = None

        self.on_item = on_item
        self.on_ok = on_ok
        self.on_fail = on_fail

    def _on_item_cb(self, i, x):
        self.on_item(i, x)

    def _on_ok_cb(self, i):
        self.on_ok(i)
        if isinstance(self.owner, gtk.Window):
            hildon.hildon_gtk_window_set_progress_indicator(self.owner, 0)

    def _on_fail_cb(self, i, e):
        self.on_fail(i, e)
        if isinstance(self.owner, gtk.Window):
            hildon.hildon_gtk_window_set_progress_indicator(self.owner, 0)

    def start(self):
        postoffice.connect('fetch', self, self._on_item_cb)
        postoffice.connect('fetch-ok', self, self._on_ok_cb)
        postoffice.connect('fetch-fail', self, self._on_fail_cb)
        if isinstance(self.owner, gtk.Window):
            hildon.hildon_gtk_window_set_progress_indicator(self.owner, 1)
        self.worker = _Worker(self.generator, self.owner)
        self.worker.start()

    def stop(self):
        postoffice.disconnect(['fetch', 'fetch-ok', 'fetch-fail'], self)

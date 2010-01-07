# Background fetcher:
# Takes a generator and a notification identifier as parameter,
# starts a thread, and post a notification whenever data arrives.
# Posts a completion notification when done.
# Terminates if generator fails or encounters an error.

import threading
from postoffice import postoffice
import jamaendo
import logging

import hildon

log = logging.getLogger(__name__)

class _Worker(threading.Thread):
    def __init__(self, generator, owner):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.generator = generator
        self.owner = owner

    def _post(self, item):
        postoffice.notify("fetch", self.owner, item)

    def _post_ok(self):
        postoffice.notify("fetch-ok", self.owner)

    def _post_fail(self, e):
        postoffice.notify("fetch-fail", self.owner, e)

    def run(self):
        try:
            for item in self.generator():
                self._post(item)
            self._post_ok()
        except jamaendo.JamendoAPIError, e:
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
        hildon.hildon_gtk_window_set_progress_indicator(self.owner, 0)

    def _on_fail_cb(self, i, e):
        self.on_fail(i, e)
        hildon.hildon_gtk_window_set_progress_indicator(self.owner, 0)

    def start(self):
        postoffice.connect('fetch', self, self._on_item_cb)
        postoffice.connect('fetch-ok', self, self._on_ok_cb)
        postoffice.connect('fetch-fail', self, self._on_fail_cb)
        hildon.hildon_gtk_window_set_progress_indicator(self.owner, 1)
        self.worker = _Worker(self.generator, self.owner)
        self.worker.start()

    def stop(self):
        postoffice.disconnect(['fetch', 'fetch-ok', 'fetch-fail'], self)

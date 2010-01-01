import cPickle, os
import logging

VERSION = 1
log = logging.getLogger(__name__)

class Settings(object):
    defaults = {
        'volume':0.5,
        'user':None,
        'favorites':set([]) # local favorites - until we can sync back
        }

    def __init__(self):
        self.__savename = "/tmp/jaemendo_uisettings"
        for k,v in self.defaults.iteritems():
            setattr(self, k, v)

    def set_filename(self, savename):
        self.__savename = savename

    def favorite(self, album):
        self.favorites.add(('album', album.ID))
        self.save()

    def load(self):
        if not os.path.isfile(self.__savename):
            return
        try:
            f = open(self.__savename)
            settings = cPickle.load(f)
            f.close()

            if settings['version'] > VERSION:
                log.warning("Settings version %s higher than current version (%s)",
                            settings['version'], VERSION)

            for k in self.defaults.keys():
                if k in settings:
                    setattr(self, k, settings[k])
        except Exception, e:
            log.exception('failed to load settings')

    def save(self):
        try:
            settings = {
                'version':VERSION,
                }
            for k in self.defaults.keys():
                settings[k] = getattr(self, k)
            f = open(self.__savename, 'w')
            cPickle.dump(settings, f)
            f.close()
        except Exception, e:
            log.exception('failed to save settings')

settings = Settings()

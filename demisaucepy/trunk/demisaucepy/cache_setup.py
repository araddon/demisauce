
from demisaucepy.cache import PylonsCache, GaeCache, DummyCache
import os, logging

log = logging.getLogger(__name__)

def load_cache():
    from demisaucepy import cache as cachemodule
    try:
        from google.appengine.api import memcache
        if 'AUTH_DOMAIN' in os.environ and 'gmail.com' in os.environ['AUTH_DOMAIN']:
            # this is pretty definitive not like the other's below
            # so we do it first
            cachemodule.cache = GaeCache()
            cachemodule.isgae = True
            log.debug('using Google App Engine Cache')
            return
    except ImportError:
        pass
    try:
        from django.core.cache import cache as djangocache
        from django.conf import settings
        if settings and settings.CACHE_BACKEND:
            cachemodule.cache = djangocache
            # not very definitive, but, nonethe less, the settings is a pretty good clue
            log.debug('In cache setup, it supports djangocache')
    except ImportError:
        try:
            from pylons import config, cache
            import pylons
            from beaker import exceptions
            if 'pylons.g' in config and config['pylons.g'] != None:
                cachemodule.cache = PylonsCache()
                log.debug('in pylons PylonsCache enabled')
            else:
                cachemodule.cache = DummyCache()
                log.debug('not django or pylons, just using dummy cache')
        except ImportError:
            cachemodule.cache = None # no cache?  or empty provider?
        
    if cachemodule.cache == None:
        log.debug('no caching was found')
        

load_cache()
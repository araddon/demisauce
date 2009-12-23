
from demisaucepy.cache import PylonsCache, GaeCache, \
    MemcacheCache, DummyCache
import os, logging
from demisaucepy import cfg


log = logging.getLogger(__name__)

def load_gae_memcache():
    try:
        from demisaucepy import cache as cachemodule
        from google.appengine.api import memcache
        if 'AUTH_DOMAIN' in os.environ and 'gmail.com' in os.environ['AUTH_DOMAIN']:
            # this is pretty definitive not like the other's below
            # so we do it first
            cachemodule.cache = GaeCache()
            cachemodule.isgae = True
            log.debug('using Google App Engine Cache')
            return True
        return False
    except ImportError:
        return False

def load_django_cache():
    try:
        from demisaucepy import cache as cachemodule
        from django.core.cache import cache as djangocache
        from django.conf import settings
        if settings and settings.CACHE_BACKEND:
            cachemodule.cache = djangocache
            # not very definitive, but, nonethe less, the settings is a pretty good clue
            log.debug('In cache setup, it supports djangocache')
            return True
        else:
            return False
    except ImportError:
        return False

def load_memcache():
    try:
        from demisaucepy import cache as cachemodule
        cachemodule.cache = MemcacheCache(cfg.CFG['memcached_servers'].split(','))
        log.debug('In cache setup, setting MemcacheCache')
        return True
    except ImportError:
        return False

def load_pylons_cache():
    try:
        from demisaucepy import cache as cachemodule
        from pylons import config, cache
        import pylons
        from beaker import exceptions
        if 'pylons.g' in config and config['pylons.g'] != None:
            cachemodule.cache = PylonsCache()
            log.debug('in pylons PylonsCache enabled')
            return True
        else:
            cachemodule.cache = DummyCache()
            log.debug('not django or pylons, just using dummy cache')
            return False
    except ImportError:
        cachemodule.cache = None # no cache?  or empty provider?
        return False

def load_cache(cachetype=None):
    from demisaucepy import cache as cachemodule
    if cachetype == None:
        if load_gae_memcache():
            return
        elif load_django_cache():
            return
        elif load_pylons_cache():
            return
        else:
            pass
    elif cachetype == 'django':
        load_django_cache()
    elif cachetype == 'gae':
        load_gae_memcache()
    elif cachetype == 'pylons':
        load_pylons_cache()
    elif cachetype == 'memcache':
        load_memcache()
    else:
        pass
    
    if cachemodule.cache == None:
        log.debug('no caching was found')
        

load_cache()
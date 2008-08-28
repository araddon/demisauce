import os, logging

cache = None

log = logging.getLogger(__name__)

def load_cache():
    try:
        from google.appengine.api import memcache
        if 'AUTH_DOMAIN' in os.environ and 'gmail.com' in os.environ['AUTH_DOMAIN']:
            # this is pretty definitive not like the other's below
            # so we do it first
            cache = GaeCache()
            log.debug('using Google App Engine Cache')
            return
    except ImportError:
        pass
    try:
        from django.core.cache import cache as djangocache
        from django.conf import settings
        if settings and settings.CACHE_BACKEND:
            cache = djangocache
            # not very definitive, but, nonethe less, the settings is a pretty good clue
            log.debug('In cache setup, it supports djangocache')
    except ImportError:
        try:
            from pylons import config, cache
            import pylons
            from beaker import exceptions
            if 'pylons.g' in config and config['pylons.g'] != None:
                cache = PylonsCache()
                log.debug('in pylons PylonsCache enabled')
            else:
                cache = DummyCache()
                log.debug('not django or pylons, just using dummy cache')
        except ImportError:
            cache = None # no cache?  or empty provider?
        
    if cache == None:
        log.debug('no caching was found')


class DummyCache(object):
    def __init__(self, *args, **kwargs):
        pass
    def add(self, *args, **kwargs):
        return True
    def get(self, key, default=None):
        return None
    def set(self, *args, **kwargs):
        pass
    def delete(self, *args, **kwargs):
        pass
    def get_many(self, *args, **kwargs):
        return {}
    def has_key(self, *args, **kwargs):
        return False


class PylonsCache(object):
    """ducktype a django cache and wrap the pylons cache
    See django api: 
    http://www.djangoproject.com/documentation/cache/
    beaker cache:
    http://docs.pylonshq.com/_sources/beaker.txt
    """
    def __init__(self):
        pass
    
    def add(self, key, value, timeout=None):
        self.set(key,value,timeout)
    
    def get(self, key, default=None):
        mycache = cache.get_cache('demisauce')
        try:
            myvalue = mycache.get_value(key)
        except KeyError:
            return None
        return myvalue
    
    def set(self, key, value, timeout=None):
        mycache = cache.get_cache('demisauce')
        mycache.set_value(key, value)
    
    def delete(self, key):
        mycache = cache.get_cache('demisauce')
        mycache.remove_value(key) 
    
    def get_many(self, keys):
        """
        Fetch a bunch of keys from the cache. For certain backends (memcached,
        pgsql) this can be *much* faster when fetching multiple values.

        Returns a dict mapping each key in keys to its value. If the given
        key is missing, it will be missing from the response dict.
        """
        d = {}
        for k in keys:
            val = self.get(k)
            if val is not None:
                d[k] = val
        return d
    
    def has_key(self, key):
        """
        Returns True if the key is in the cache and has not expired.
        """
        return self.get(key) is not None
    
    def __contains__(self, key):
        """
        Returns True if the key is in the cache and has not expired.
        """
        # This is a separate method, rather than just a copy of has_key(),
        # so that it always has the same functionality as has_key(), even
        # if a subclass overrides it.
        return self.has_key(key)
    

class GaeCache(object):
    """
    ducktype a django cache and wrap the gae memcache
    See django api: 
    http://www.djangoproject.com/documentation/cache/
    google app engine memcached:
    http://code.google.com/appengine/docs/memcache/
    """
    def __init__(self):
        pass
    
    def add(self, key, value, timeout=None):
        self.set(key,value,timeout)
    
    def get(self, key, default=None):
        val = memcache.get(key)
        if val == none and default is not None:
            return default
        else:
            return val
        
    
    def set(self, key, value, timeout=None):
        memcache.add(key=key, value=value, time=timeout)
    
    def delete(self, key):
        return memcache.delete(key)
    
    def get_many(self, keys):
        """
        Fetch a bunch of keys from the cache. For certain backends (memcached,
        pgsql) this can be *much* faster when fetching multiple values.

        Returns a dict mapping each key in keys to its value. If the given
        key is missing, it will be missing from the response dict.
        """
        d = {}
        for k in keys:
            val = self.get(k)
            if val is not None:
                d[k] = val
        return d
    
    def has_key(self, key):
        """
        Returns True if the key is in the cache and has not expired.
        """
        return self.get(key) is not None
    
    def __contains__(self, key):
        """
        Returns True if the key is in the cache and has not expired.
        """
        # This is a separate method, rather than just a copy of has_key(),
        # so that it always has the same functionality as has_key(), even
        # if a subclass overrides it.
        return self.has_key(key)
    



load_cache()


import os, logging
try:
    from google.appengine.api import memcache
except ImportError:
    pass
try:
    from django.core.cache import cache as djangocache
    from django.conf import settings
except ImportError:
    pass
try:
    from pylons import config
    from pylons import cache as pylonscache
    import pylons
    from beaker import exceptions
except ImportError:
    pass

cache = None
isgae = False

log = logging.getLogger(__name__)


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

class CacheBase(object):
    """ducktype a django cache"""
    def add(self, key, value, timeout=None):
        self.set(key,value,timeout)
    
    def get(self, key, default=None):
        raise NotImplementedError
    
    def set(self, key, value, timeout=None):
        raise NotImplementedError
    
    def delete(self, key):
        raise NotImplementedError
    
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
    

                
class PylonsCache(CacheBase):
    """ducktype a django cache and wrap the pylons cache
    See django api: 
    http://www.djangoproject.com/documentation/cache/
    beaker cache:
    http://docs.pylonshq.com/_sources/beaker.txt
    """
    def get(self, key, default=None):
        mycache = pylonscache.get_cache('demisauce')
        try:
            myvalue = mycache.get_value(key)
        except KeyError:
            return None
        return myvalue
    
    def set(self, key, value, timeout=None):
        mycache = pylonscache.get_cache('demisauce')
        mycache.set_value(key, value)
    
    def delete(self, key):
        mycache = pylonscache.get_cache('demisauce')
        mycache.remove_value(key) 
    

class GaeCache(object):
    """
    ducktype a django cache and wrap the gae memcache
    See django api: 
    http://www.djangoproject.com/documentation/cache/
    google app engine memcached:
    http://code.google.com/appengine/docs/memcache/
    """
    def get(self, key, default=None):
        val = memcache.get(key)
        if val == None and default is not None:
            return default
        else:
            return val
        
    
    def set(self, key, value, timeout=0):
        return  memcache.add(key, value, timeout)
    
    def delete(self, key):
        return memcache.delete(key)
    




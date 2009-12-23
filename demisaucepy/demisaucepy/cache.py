"""
This code [especially CacheBase] is from Django, so that license is
intact
"""
import os, logging
try:
    from google.appengine.api import memcache as gaememcache
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
    
try:
    import cmemcache as memcache
except ImportError:
    try:
        import memcache
    except:
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
    """ducktype a django cache
    Credits:  Django:
    http://code.djangoproject.com/browser/django/trunk/django/core/cache/backends/base.py
    """
    def __init__(self,default_timeout = 300):
        self.default_timeout = default_timeout
    
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
    

class MemcacheCache(CacheBase):
    def __init__(self, servers, default_timeout = 300):
        super(MemcacheCache,self).__init__(default_timeout = default_timeout)
        self._cache = memcache.Client(servers,debug=0)
    
    def add(self, key, value, timeout=0):
        return self._cache.add(key, value, timeout or self.default_timeout)
    
    def get(self, key, default=None):
        val = self._cache.get(key)
        if val is None:
            return default
        else:
            return val
    
    def set(self, key, value, timeout=0):
        self._cache.set(key, value, timeout or self.default_timeout)
    
    def delete(self, key):
        self._cache.delete(key)
    
    def get_many(self, keys):
        return self._cache.get_multi(keys)
    
    def close(self, **kwargs):
        self._cache.disconnect_all()
    

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
            return default
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
        val = gaememcache.get(key)
        if val == None:
            return default
        else:
            return val
        
    
    def set(self, key, value, timeout=0):
        return  gaememcache.add(key, value, timeout)
    
    def delete(self, key):
        return gaememcache.delete(key)
    



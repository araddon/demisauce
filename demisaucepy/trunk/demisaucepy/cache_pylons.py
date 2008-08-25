from pylons import cache
import pylons
from beaker import exceptions

class PylonsCache(object):
    """ducktype a django cache and wrap the pylons cache
    See django api: 
    http://www.djangoproject.com/documentation/cache/
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
        self.set(key,None)
    
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
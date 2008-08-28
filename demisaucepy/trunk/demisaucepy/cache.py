import os

cache = None

env = {'django':False,'gae':False,'pylons':False}

def load_cache():
    try:
        from google.appengine.api import memcache
        if 'AUTH_DOMAIN' in os.environ and 'gmail.com' in os.environ['AUTH_DOMAIN']:
            # this is very definitive not the other's below
            cache = None# tbd
            print 'is gae '
            return
    except ImportError:
        pass
    try:
        from django.core.cache import cache as djangocache
        from django.conf import settings
        if settings and settings.CACHE_BACKEND:
            cache = djangocache
            # not very definitive
        print 'In django, using djangocache'
    except ImportError:
        try:
            from pylons import config
            if 'pylons.g' in config and config['pylons.g'] != None:
                from demisaucepy import cache_pylons
                cache = cache_pylons.PylonsCache()
                print 'in pylons PylonsCache enabled'
            else:
                from demisaucepy import cache_pylons
                cache = cache_pylons.DummyCache()
                print 'not django or pylons, just using dummy cache'
        except ImportError:
            cache = None # no cache?  or empty provider?
        
    if cache == None:
        print 'no cache'




load_cache()




cache = None

try:
    from django.core.cache import cache as djangocache
    from django.conf import settings
    if settings and settings.CACHE_BACKEND:
        cache = djangocache
    print 'yes, in djangocache'
except ImportError:
    print 'nope, django cache not imported'
    try:
        from demisaucepy import cache_pylons
        cache = cache_pylons.PylonsCache()
    except ImportError:
        cache = None # no cache?  or empty provider?
        
if cache == None:
    raise 'eh'



#!/usr/bin/env python
import tornado.ioloop
import tornado.options
import os, logging, functools
from tornado.options import define, options
import demisaucepy
from demisaucepy.cache import DummyCache, MemcacheCache
import demisauce
from demisauce import model

log = logging.getLogger("demisauce")

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))


class AppBase():
    def __init__(self):
        # setup demisauce server config
        options.site_root = SITE_ROOT
        
        # create scheduler
        from demisauce.lib import scheduler
        self.scheduler = scheduler.start()
        
        memcache_cache = MemcacheCache(options.memcached_servers)
        # Have one global connection to the DB across app
        self.db = model.get_database(cache=memcache_cache)
        log.debug("gearman_servers = %s" % options.gearman_servers)


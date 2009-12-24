#!/usr/bin/env python
import tornado.ioloop
import tornado.options
import os, logging, functools
from tornado.options import define, options
from demisaucepy.cache import DummyCache, MemcacheCache
import demisauce
import demisaucepy
from demisauce import model

__version__ = '0.1.1'
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
#SITE_ROOT = os.path.realpath(SITE_ROOT + '' )
#print("SITE_ROOT = %s" % SITE_ROOT)

define("facebook_api_key", help="your Facebook application API key",
        default="1c9724431c6a5ebb2167b87862373776")
define("facebook_secret", help="your Facebook application secret",
        default="13c61611ccac41a95cbfe9a940b0afbd")
define("twitter_consumer_key", help="your Twitter application API key",
        default="7xjPzAjqtH5QqitEicaFqQ")
define("twitter_consumer_secret", help="your Twitter application secret",
        default="g9Wg0fDCcFN4IGtJ8PB9TYq5RiRMEPSfqZ3MkcPPl9Y")
define("base_url", default="http://localhost:4950", help="base fq url, no trailing slash to site")
define("port", default=4950, help="run on the given port", type=int)

"""
define("site_root", default=SITE_ROOT, help="Root Path of site, set at runtime")
define("redis_host", default="192.168.1.7",help="List of redis hosts:  192.168.1.1:5555,etc",multiple=False)
define("gearman_servers",default="192.168.1.7",multiple=True,help="gearman hosts format host:port,host:port")
define("memcached_servers", default="192.168.1.7:11211",multiple=True, help="list of memcached servers")
#define("solr_server",default="http://192.168.1.5:8080/lf")
define("solr_server",default="http://192.168.1.9:8080/dssolr",help="http url and path of solr server")
define("asset_url",default="http://assets.selwayfoods.com", help="fq url to asset address")
define("demisauce_url",default="http://localhost:4950", help="path to demisauce server")
define("demisauce_api_key",default="5c427992131479acb17bcd3e1069e679",help="api key")
define("demisauce_admin",default="demisauce@demisauce.org",help='email address of demisauce admin')
define("email_from",default="demisauce@demisauce.org",help="default email from address")
define("smtp_username",default="demisauce@demisauce.org",help="smtp username")
define("smtp_password",default="NOTREAL",help="pwd")
define("smtp_server",default="smtp.gmail.com",help="smtp address")

"""

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
        logging.debug("gearman_servers = %s" % options.gearman_servers)

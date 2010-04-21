# -*- coding: utf-8 -*-
#!/usr/bin/env python
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.escape
from tornado.options import define, options
import os, logging, functools
import jinja2 
#from demisaucepy import options as dsoptions
import demisaucepy.options
import demisauce
tornado.options.parse_command_line() # must force load of options for metaclass
from demisaucepy import cache_setup
from demisaucepy.cache import DummyCache, MemcacheCache
cache_setup.load_cache()
import demisauce
from demisauce import model
from demisauce.lib.cacheextension import FragmentCacheExtension
import demisaucepy
from demisauce.lib import helpers
from demisauce.appbase import AppBase


SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.realpath(SITE_ROOT + '/../../' )
if "/Users" in SITE_ROOT:
    db_root = os.path.realpath(PROJECT_ROOT + '/database/' )
else:
    db_root = os.path.realpath(SITE_ROOT + '/' )


class Jinja2Environment( jinja2.Environment ):
    def load( self, template_path):
        tmpl = self.get_template( template_path )
        if tmpl:
            setattr(tmpl, "generate", tmpl.render)
        return tmpl
    


class Application(tornado.web.Application):
    def __init__(self):
        template_path = os.path.join(os.path.dirname(__file__), "demisauce/views")
        
        # create scheduler
        from demisauce.lib import scheduler
        self.scheduler = scheduler.start()
        
        # Have one global connection to the DB across app
        memcache_cache = MemcacheCache(options.memcached_servers)
        self.db = model.get_database(cache=memcache_cache)
        
        logging.debug("gearman_servers = %s" % options.gearman_servers)
        settings = {
            "title": u"Local 151",
            "template_path": template_path,
            "static_path":os.path.join(os.path.dirname(__file__), "demisauce/static"),
            "xsrf_cookies": False,
            "cookie_secret":"32oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            "login_url":"/user/signin",
            "redis_host":options.redis_host,
            "demisauce_url":options.demisauce_url,
            "asset_url":options.asset_url,
            "oauth_callback":("%saccount/" % options.base_url),
            "debug":options.debug,
            "base_url":options.base_url,
            "twitter_consumer_key":options.twitter_consumer_key,
            "twitter_consumer_secret":options.twitter_consumer_secret,
            "facebook_api_key":options.facebook_api_key,
            "facebook_secret":options.facebook_secret,
            "sqlalchemy_default_url":options.sqlalchemy_default_url,
            "sqlalchemy_default_echo":options.sqlalchemy_default_echo,
            #"template_path":template_path, 
        }## "ui_modules": {"Entry": EntryModule},
        
        from demisauce import controllers
        _handlers = [] + controllers._controllers
        from demisauce.controllers import account, home, dashboard, template,\
            admin, site, api, service
        
        _handlers += account._controllers + \
            home._controllers + dashboard._controllers + template._controllers + \
            admin._controllers + site._controllers + api._controllers + \
            service._controllers
        
        from demisauce.controllers import CustomErrorHandler
        self.error_handler = CustomErrorHandler
        
        jinja_env = Jinja2Environment(loader=jinja2.FileSystemLoader(template_path),
                                        extensions=[FragmentCacheExtension])
        #jinja_env.fragment_cache = DummyCache() 
        jinja_env.fragment_cache = memcache_cache
        # custom filters etc
        jinja_env.filters.update(helpers._filters)
        settings.update({"jinja2_env":jinja_env})
        
        # start web app
        tornado.web.Application.__init__(self, _handlers, **settings)
            

def main():
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

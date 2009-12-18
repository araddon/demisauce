# -*- coding: utf-8 -*-
#!/usr/bin/env python
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.escape
import os, logging, functools
from demisauce import model
from tornado.options import define, options
import jinja2 
from demisauce.lib.cacheextension import FragmentCacheExtension
from demisaucepy.cache import DummyCache, MemcacheCache
from demisauce.lib import helpers

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.realpath(SITE_ROOT + '/../../' )
if "/Users" in SITE_ROOT:
    db_root = os.path.realpath(PROJECT_ROOT + '/database/' )
else:
    db_root = os.path.realpath(SITE_ROOT + '/' )



define("site_root", default=SITE_ROOT, help="Root Path of site")
define("port", default=4950, help="run on the given port", type=int)
define("facebook_api_key", help="your Facebook application API key",
        default="1c9724431c6a5ebb2167b87862373776")
define("facebook_secret", help="your Facebook application secret",
        default="13c61611ccac41a95cbfe9a940b0afbd")
define("twitter_consumer_key", help="your Twitter application API key",
        default="7xjPzAjqtH5QqitEicaFqQ")
define("twitter_consumer_secret", help="your Twitter application secret",
        default="g9Wg0fDCcFN4IGtJ8PB9TYq5RiRMEPSfqZ3MkcPPl9Y")
define("base_url", default="http://localhost:4950")
define("redis_host", default="192.168.1.7")
define("gearman_servers",default="192.168.1.7")
define("memcached_servers", default="192.168.1.7:11211")
#define("solr_server",default="http://192.168.1.5:8080/lf")
define("solr_server",default="http://192.168.1.9:8080/dssolr")
define("demisauce_url",default="http://localhost:4950")
define("asset_url",default="http://assets.selwayfoods.com")
define("demisauce_api_key",default="5c427992131479acb17bcd3e1069e679")

class Jinja2Environment( jinja2.Environment ):
    def load( self, template_path):
        tmpl = self.get_template( template_path )
        if tmpl:
            setattr(tmpl, "generate", tmpl.render)
        return tmpl
    


class Application(tornado.web.Application):
    def __init__(self):
        from demisauce import controllers
        _handlers = [] + controllers._controllers
        from demisauce.controllers import account, home,dashboard,email,admin, \
            site

        _handlers += account._controllers + \
            home._controllers + dashboard._controllers + email._controllers + \
            admin._controllers + site._controllers
        
        template_path = os.path.join(os.path.dirname(__file__), "demisauce/templates")
        logging.debug("template_path = %s" % template_path)
        jinja_env = Jinja2Environment(loader=jinja2.FileSystemLoader(template_path),
                                        extensions=[FragmentCacheExtension])
        
        
        #jinja_env.fragment_cache = DummyCache() 
        jinja_env.fragment_cache = MemcacheCache(options.memcached_servers.split(";"))
        from demisauce.controllers import CustomErrorHandler
        self.error_handler = CustomErrorHandler
        
        # create scheduler
        from demisauce.lib import scheduler
        self.scheduler = scheduler.start()
        
        options.gearman_servers = options.gearman_servers.split(',')
        logging.debug("gearman_servers = %s" % options.gearman_servers)
        settings = {
            "title": u"Local 151",
            "template_path": template_path,
            "static_path":os.path.join(os.path.dirname(__file__), "demisauce/public"),
            "xsrf_cookies": True,
            "cookie_secret":"32oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            "login_url":"/account/signin",
            "redis_host":options.redis_host,
            "demisauce_url":options.demisauce_url,
            "asset_url":options.asset_url,
            "oauth_callback":("%saccount/" % options.base_url),
            "debug":True,
            "base_url":options.base_url,
            "twitter_consumer_key":options.twitter_consumer_key,
            "twitter_consumer_secret":options.twitter_consumer_secret,
            "facebook_api_key":options.facebook_api_key,
            "facebook_secret":options.facebook_secret,
            "sqlalchemy_default_url":options.sqlalchemy_default_url,
            "sqlalchemy_default_echo":options.sqlalchemy_default_echo,
            #"template_path":template_path, 
            "jinja2_env":jinja_env,
        }## "ui_modules": {"Entry": EntryModule},
        tornado.web.Application.__init__(self, _handlers, **settings)

        # Have one global connection to the DB across app
        self.db = model.get_database(settings,cache=jinja_env.fragment_cache)
        # custom filters etc
        jinja_env.filters.update(helpers._filters)
    

def main():
    tornado.options.parse_command_line()
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

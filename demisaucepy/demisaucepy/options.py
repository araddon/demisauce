from tornado.options import options,define

define("site_root", default="/home/demisauce", help="Root Path of site, set at runtime")
define("redis_host", default="127.0.0.1",help="List of redis hosts:  192.168.1.1:5555,etc",multiple=False)
define("gearman_servers",default=["127.0.0.1"],multiple=True,help="gearman hosts format host:port,host:port")
define("solr_server",default="http://127.0.0.1:8080/dssolr",help="http url and path of solr server")
define("asset_url",default="http://assets.yourdomain.com", help="fq url to asset address")
define("demisauce_url",default="http://localhost:4950", help="path to demisauce server from client")
define("demisauce_server_url",default="http://1270.0.01:4950", 
    help="path to demisauce server (can be private ip)")
define("demisauce_api_key",default="5c427992131479acb17bcd3e1069e679",help="api key")
define("demisauce_admin",default="demisauce@demisauce.org",help='email address of demisauce admin')
define("demisauce_domain",default="localhost",help='Domain to set cookie on')


define("memcached_servers", default=["127.0.0.1:11211"],multiple=True, help="list of memcached servers")
define("demisauce_cache", default="memcache", 
        help="type of cache (memcache|pylons|gae|django|redis|dummy)")
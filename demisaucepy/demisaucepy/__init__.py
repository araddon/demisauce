import urllib, urllib2, os, sys, logging
import string
import httpfetch
import json
import datetime
from demisaucepy import xmlrpcreflector
from tornado.options import options,define
import demisaucepy.cache_setup
import hashlib
import warnings
import xmlrpclib
import re
import tornado
from tornado.options import options, define

log = logging.getLogger(__name__)

__version__ = '0.1.1'

DATETIME_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(\.\d+)?Z$')

define("site_root", default="/home/demisauce", help="Root Path of site, set at runtime")
define("redis_host", default="192.168.1.7",help="List of redis hosts:  192.168.1.1:5555,etc",multiple=False)
define("gearman_servers",default=["192.168.1.7"],multiple=True,help="gearman hosts format host:port,host:port")
define("solr_server",default="http://192.168.1.9:8080/dssolr",help="http url and path of solr server")
define("asset_url",default="http://assets.yourdomain.com", help="fq url to asset address")
define("demisauce_url",default="http://localhost:4950", help="path to demisauce server")
define("demisauce_api_key",default="5c427992131479acb17bcd3e1069e679",help="api key")
define("demisauce_admin",default="demisauce@demisauce.org",help='email address of demisauce admin')

define("memcached_servers", default=["192.168.1.7:11211"],multiple=True, help="list of memcached servers")
define("demisauce_cache", default="memcache", 
        help="type of cache (memcache|pylons|gae|django|redis|dummy)")


class RetrievalError(Exception):
    def __init__(self,message="There was an error retrieving this message"):
        self.message = message

def LoadConfig(file, config={}):
    """
    returns a dictionary with key's of the ini file
    """
    conf_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_file = os.path.join(conf_dir, file)
    config = config.copy()
    cp = ConfigParser.ConfigParser()
    cp.read(ini_file)
    for sec in cp.sections():
        name = string.lower(sec)
        for opt in cp.options(sec):
            config[string.lower(opt)] = string.strip(cp.get(sec, opt))
    return config

def hash_email(email):
    return hashlib.md5(email.lower()).hexdigest()

def args_substitute(url_format,sub_dict):
    for k in sub_dict.keys():
        if sub_dict[k] is not None:
            url_format = url_format.replace('{%s}'%k,sub_dict[k])
    return url_format 

class jsonwrapper(dict):
    def __init__(self,jsonval):
        self.index = 0
        self._json_list = None
        self._json_dict = None
        
        if isinstance(jsonval,str):
            jsonval = json.loads(jsonval)
        if isinstance(jsonval,dict):
            self._json_dict = jsonval
        elif isinstance(jsonval,list):
            self._json_list = jsonval
        else:
            raise Exception("how can it be none list, dict?")
        if self._json_list:
            self.index = len(self._json_list)
    
    def __iter__(self):
        return self
    
    def next(self):
        if self.index == 0:
            raise StopIteration
        self.index = self.index - 1
        val = self._json_list[self.index]
        return self._to_python(val)
    
    def __len__(self):
        if self._json_list:
            return len(self._json_list)
        elif self._json_dict:
            return len(self._json_dict)
        return 0
    
    def __getattr__(self, name):
        if self._json_dict:
            return self._to_python(self._json_dict[name])
        else:
            raise KeyError
    
    def __getitem__(self, name):
        if self._json_dict:
            val = self._json_dict[name]
        elif self._json_list and type(name) == int:
            val = self._json_list[name]
        else:
            raise KeyError
        
        return self._to_python(val)
    
    def _to_python(self,val):
        if val is None:
            return val
        
        if isinstance(val, (int, float, long, complex)):
            return val
        
        if isinstance(val,dict):
            return jsonwrapper(val)
        elif isinstance(val, (list)):
            return jsonwrapper(val)
        elif isinstance(val,(tuple)):
            return val
        
        if val == 'true':
            return True
        elif val == 'false':
            return False
        
        if isinstance(val, basestring):
            possible_datetime = DATETIME_REGEX.search(val)
            
            if possible_datetime:
                date_values = possible_datetime.groupdict()
                
                for dk, dv in date_values.items():
                    date_values[dk] = int(dv)
                
                return datetime(date_values['year'], date_values['month'], date_values['day'], date_values['hour'], date_values['minute'], date_values['second'])
        
        # else, probably string?
        return val
    
    def _from_python(self, value):
        """
        Converts python values to a form suitable for insertion into the xml
        we send to solr.
        """
        if isinstance(value, datetime):
            value = value.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif isinstance(value, date):
            value = value.strftime('%Y-%m-%dT00:00:00Z')
        elif isinstance(value, bool):
            if value:
                value = 'true'
            else:
                value = 'false'
        else:
            value = unicode(value)
        return value
    
    def _to_pythonOLD(self, value):
        """
        Converts values from Solr to native Python values.
        """
        if isinstance(value, (int, float, long, complex)):
            return value
        
        if isinstance(value, (list, tuple)):
            value = value[0]
        
        if value == 'true':
            return True
        elif value == 'false':
            return False
        
        if isinstance(value, basestring):
            possible_datetime = DATETIME_REGEX.search(value)
        
            if possible_datetime:
                date_values = possible_datetime.groupdict()
            
                for dk, dv in date_values.items():
                    date_values[dk] = int(dv)
            
                return datetime(date_values['year'], date_values['month'], date_values['day'], date_values['hour'], date_values['minute'], date_values['second'])
        
        try:
            # This is slightly gross but it's hard to tell otherwise what the
            # string's original type might have been. Be careful who you trust.
            converted_value = eval(value)
            
            # Try to handle most built-in types.
            if isinstance(converted_value, (list, tuple, set, dict, int, float, long, complex)):
                return converted_value
        except:
            # If it fails (SyntaxError or its ilk) or we don't trust it,
            # continue on.
            pass
        
        return value
    

class ServiceDefinition(object):
    """
    service definition used by ServiceClient for a remote service.   
    Accepts everything by paramaters or accepts {name,format,app_slug} and 
    load the rest of the definition from demisauce service definition
    
    :name: name of remote service
    :format: format (json,xml,html,rss) of remote service
    :app_slug: url friendly name of app  (demisauce,phpdemo,djangodemo):  entered
        into web admin when signing up
    :cache: True/False to use cache default = True
    :cache_time: in seconds, default = 15 minutes
    :method_url:  url part of this service (many services/app=base_url)
    :url_format:  a simple string substitution of any of available values
    :api_key: secret api key for service
    :data: dict of name/value pair's to be added to request  (get/post)
    :base_url:  base url of the "app" (each app has many services, 
        shared base_url) ex:  http://demisauce.demisauce.com
        note, NOT trailing slash
    :cache:  default = True, to use cache or not
    """
    _service_keys = ['name']
    def __init__(self, name,format='json', data={},app_slug='demisauce',
            base_url=None,api_key=None,local_key='id',cache=True,cache_time=900):
        self.name = name
        self.format = format
        self.app_slug = app_slug
        self.url = "{base_url}/api/{service}/{key}.{format}?apikey={api_key}"
        self.cache = cache
        self.cache_time = cache_time # 15 minutes
        self.url_format = "{base_url}/api/{service}/{key}.{format}?apikey={api_key}"
        self.data = data
        self.isdefined = False
        self.needs_service_def = True
        self.method_url = None
        self.service_registry = None
        self.api_key = api_key
        self.base_url = base_url
        if api_key == None:
            self.api_key = options.demisauce_api_key
        if base_url == None:
            self.base_url = options.demisauce_url
    
    def substitute_args(self,pattern,data={},request=''):
        """Create a dictionary of all name/value pairs
        you could reasonably expect to use in substitution"""
        data.update({"base_url":self.base_url,
            "format":self.format,
            "service":self.name,
            "key":request, 
            "request":request,
            "app_slug":self.app_slug,
            "api_key":self.api_key})
        #print('substituteargs = %s' % (data))
        return args_substitute(pattern, data)
    
    def get_url(self,request):
        urlformat = ''
        if self.format == 'xmlrpc':
            urlformat = self.base_url
        elif self.method_url is not None and self.method_url != "None" and \
            self.method_url.find('{base_url}') < 0:
            # use service.method_url not url_format
            if self.method_url.find('/') == 0:
                urlformat =  '{base_url}%s' % (self.method_url)
            else:
                urlformat =  '{base_url}/%s' % (self.method_url)
        else:
            urlformat = self.url_format
        url = ''
        try:
            url = self.substitute_args(urlformat,request=request)
        except AttributeError, e:
            raise RetrievalError('Attribute URL problems')
        return url
    
    def clone(self):
        """Create a clone of this service definition"""
        ns = ServiceDefinition(name=self.name)
        ns.format = self.format
        ns.app_slug = self.app_slug
        ns.data = self.data
        ns.cache = self.cache
        ns.cache_time = self.cache_time
        ns.isdefined = self.isdefined
        ns.needs_service_def = False
        ns.api_key = self.api_key
        ns.base_url = self.base_url
        return ns
    
    def load_definition(self,request_key='demisauce/comment'):
        """
        The service is partially defined through demisauce
        web service, partly local declaration, rest of definition
        is loaded once at startup with this and cached as part of the 
        python in memory class definition
        """
        #log.debug('ServiceDefinition.load_definitin() %s:%s ' % (self.app_slug, request_key))
        self.service_registry = self.clone()
        self.service_registry.format = 'json'
        self.service_registry.url_format = "{base_url}/api/{service}/{key}.{format}?apikey={api_key}"
        self.service_registry.name = 'service'
        client = ServiceClient(service=self.service_registry)
        client.use_cache = self.cache
        #client.connect()
        #client.authorize()
        response = client.fetch_service(request=self.name)
        #print response.data
        # setup more service definition
        #log.debug('after service load %s, %s' % (self.app_slug, self.name))
        jsondata = None
        if response.json and len(response.json) == 1:
            jsondata = response.json[0]
        else:
            logging.error("Json return len sould be 1 %s" % response.json)
            raise Exception("Json return len sould be 1 %s" % response.json)
        self.isdefined = True
        if jsondata and 'url' in jsondata:
            #print dir(model)
            if 'site' in jsondata and 'base_url' in jsondata['site']:
                self.base_url = jsondata['site']['base_url']
            #log.debug('setting base_url to%s for%s %s ' % (self.base_url, self.app_slug, self.name))
            if 'method_url' in jsondata and jsondata['method_url'] != 'None':
                self.method_url = jsondata['method_url']
            if 'url_format' in jsondata and jsondata['url_format'] != 'None':
                self.url_format = jsondata['url_format']
            else:
                self.url_format = None
            if 'format' in jsondata and jsondata['format'] != 'None':
                self.format = jsondata['format']
            if 'cache_time' in jsondata and jsondata['cache_time'] != 'None':
                self.cache_time = jsondata['cache_time']
            
        else:
            log.debug('no base url on service definition get')
        
    
    def __str__(self):
        return "{name:'%s',format:'%s',base_url:'%s'}" % (self.name,self.format,self.base_url)
    

class ServiceResponse(object):
    def __init__(self,format='json'):
        self.success = False
        self.data = None
        self.xmlrpc = None
        self.message = ''
        self.name = 'name'
        self.format = 'json'
        self.__xmlnode__ = None
        self.url = ''
        self.json = None
        self.status = 0
    
    def handle_response(self):
        pass
    
    def get_xmlnode(self):
        if self.__xmlnode__ == None and self.data != None:
            self.__xmlnode__ = XMLNode(self.data)
            return self.__xmlnode__
        elif self.__xmlnode__ is not None:
            return self.__xmlnode__
        else:
            return None
    
    xmlnode = property(get_xmlnode)
    
    def getmodel(self):
        if self.format == 'xmlrpc':
            return self.xmlrpc
        elif self.__xmlnode__ == None and self.data != None:
            # probably need to verify we can parse this?
            self.__xmlnode__ = XMLNode(self.data)
            if self.__xmlnode__:
                    if self.__xmlnode__._xmlhash:
                        if len(self.__xmlnode__._xmlhash.keys()) == 1:
                            # if only one, thats undoubtedly it
                            self.name = self.__xmlnode__._xmlhash.keys()[0]
                            return self.__xmlnode__._xmlhash[self.name]
            if self.__xmlnode__ and self.name in self.__xmlnode__._xmlhash:
                return self.__xmlnode__._xmlhash[self.name]
            return self.__xmlnode__
        elif self.__xmlnode__ is not None:
            return self.__xmlnode__
        else:
            return None
    
    model = property(getmodel)


class ServiceTransportBase(object):
    def __init__(self,service=None):
        self.service = service
        self.connected = False
        self.authorized = False
    
    def connect(self):
        raise NotImplementedError
    def fetch(self):
        raise NotImplementedError

class GaeServiceTransport(ServiceTransportBase):
    def fetch(self):
        raise NotImplementedError
    

class GAEXMLRPCTransport(object):
    """Handles an HTTP transaction to an XML-RPC server.
    From:   http://brizzled.clapper.org/id/80
    """
    def __init__(self):
        pass
    
    def request(self, host, handler, request_body, verbose=0):
        from google.appengine.api import urlfetch
        result = None
        url = 'http://%s%s' % (host, handler)
        try:
            response = urlfetch.fetch(url,
                                      payload=request_body,
                                      method=urlfetch.POST,
                                      headers={'Content-Type': 'text/xml'})
        except:
            msg = 'Failed to fetch %s' % url
            logging.error(msg)
            raise xmlrpclib.ProtocolError(host + handler, 500, msg, {})
        
        if response.status_code != 200:
            logging.error('%s returned status code %s' %
                          (url, response.status_code))
            raise xmlrpclib.ProtocolError(host + handler,
                                          response.status_code,
                                          "",
                                          response.headers)
        else:
            result = self.__parse_response(response.content)
        
        return result
    
    def __parse_response(self, response_body):
        p, u = xmlrpclib.getparser(use_datetime=False)
        p.feed(response_body)
        return u.close()
    

class XmlRpcServiceTransport(ServiceTransportBase):
    def __init__(self, request=None,**kwargs):
        super(XmlRpcServiceTransport, self).__init__(**kwargs)
        self.request = request
    
    #http://svn.python.org/projects/python/trunk/Lib/xmlrpclib.py
    def fetch(self,url,data={},extra_headers={},response=None):
        #print('in xmlrpcservicetransport: %s' % url)
        response = response or ServiceResponse()
        if httpfetch.ISGAE == True:
            rpc_server = xmlrpclib.ServerProxy(url,
                                           GAEXMLRPCTransport())
        else:
            rpc_server = xmlrpclib.ServerProxy(url)
        #response.data = rpc_server.wp.getPages(1,'admin','admin')
        #response.data = rpc_server.blogger.getUsersBlogs('','admin','admin')
        #response.data = rpc_server.metaWeblog.getRecentPosts(1,'admin', 'admin', 5)
        #response.data = getattr(getattr(rpc_server,'metaWeblog'),'getRecentPosts')(1,'admin', 'admin', 5)
        #print('inXmlRpcTransport.fetch data=%s' % (data))
        #print('inXmlRpcTransport.fetch method_url=%s' % (self.service.method_url))
        # wp.getPage,{blog_id},{request},{user},{password}
        args = self.service.substitute_args(self.service.method_url,data=data,request=self.request)
        args = args.split(',')
        if len(args) > 0:
            method = args[0]
            t = tuple([s for s in args[1:]])
            #response.data = getattr(rpc_server,'metaWeblog.getRecentPosts')(t)
            #print('inXmlRpcTransport.fetch args=%s' % (args))
            response.data = getattr(rpc_server,method)(t)
            #print('In XmlrpcFetch, data= %s' % (response.data))
            response.format = 'xmlrpc'
            response.xmlrpc = xmlrpcreflector.parse_result(response.data)
        response.success = True
        #print('exiting xmlrpc.fetch')
        return response
    

class HttpServiceTransport(ServiceTransportBase):
    def connect(self):
        pass
    
    def fetch(self,url,data={},extra_headers={},response=None,http_method='GET'):
        response = response or ServiceResponse()
        useragent = 'DemisaucePY/1.0'
        try: 
            #log.debug('httptransport getting url: %s' % (url))
            response.params = httpfetch.fetch(url, data=data,agent=useragent,extra_headers=extra_headers,http_method=http_method)
            response.status = response.params['status']
            if response.params['status'] == 500:
                response.message = 'there was an error on the demisauce server, \
                        no content was returned'
                log.error('500 = %s' % url)
            elif response.params['status'] == 404:
                response.message = 'not found'
                log.debug('404 = %s' % url)
            elif response.params['status'] == 401:
                response.message = 'Invalid API Key'
                log.debug('401 = %s' % url)
            else:
                response.data = response.params['data']
                response.success = True
                response.message = 'success'
        except urllib2.URLError, err:
            if err[0][0] == 10061:
                #print 'error in demisauce_fetch'
                log.debug('No Server = %s' % url)
                # connection refused
                response.message = 'the remote server didn\'t respond at \
                        <a href=\"%s\">%s</a> ' % (url,url)
                        
        if hasattr(response,'handle_response'):
            response.handle_response()
        return response
    

class OAuthServiceTransport(HttpServiceTransport):
    def connect(self):
        raise NotImplementedError
    def fetch(self):
        raise NotImplementedError

# ServiceClient pseudo interface
class ServiceClientBase(object):
    def connect(self):
        raise NotImplementedError
    def authorize(self):
        raise NotImplementedError
    def fetch_service(self):
        raise NotImplementedError

class ServiceClient(ServiceClientBase):
    """
    ::
        client = ServiceClient(service=ServiceDefinition(
            name='feedback_badge',
            format='xml',
            app_slug='demisauce'
        ))
        client.fetch_service(request=resource)
        return client.response.data
    """
    def __init__(self,service,transport=None):
        self.service = service # ServiceDefinition
        self.transport = transport or HttpServiceTransport()
        self.transport.service = service
        self.extra_headers = {}
        self.use_cache = True
        self.request = 'service'
        self.response = ServiceResponse(format=service.format)
        self._cache_key = None
    
    def connect(self,request='service',headers={}):
        self.transport.connect(request=request)
    
    def authorize(self):
        pass
    
    def cache_key(self,url):
        if self._cache_key:
            return self._cache_key
        cache_key = url
        #TODO:  allow non vary by headers?
        for key in self.extra_headers:
            cache_key += '%s:%s' % (key,self.extra_headers[key])
        cache_key = hashlib.md5(cache_key.lower()).hexdigest()
        #print 'md5cachekey = %s' % (cache_key)
        self._cache_key = cache_key
        return cache_key
    
    def check_cache(self,cache_key):
        """
        """
        
        import demisaucepy.cache_setup
        from demisaucepy.cache import cache
        if self.use_cache == False:
            return False
        if cache == None:
            #log.debug('doesnt use cache')
            return False
        
        #log.debug('checking cache key=%s' % cache_key)
        cacheval = None
        #cache.delete(cache_key)
        cacheval = cache.get(cache_key)
        if cacheval != None:
            log.debug('cache found for = %s' % (cache_key))
            #self.response.data = cacheval.data
            self.response = cacheval
            return True
        else:
            log.debug('cache NOT found for = %s' % (cache_key))
            return False
    
    def fetch_service(self,request=None,data={},http_method='GET'):
        #self.connect(request=request)
        #self.authorize()
        import demisaucepy.cache_setup
        from demisaucepy.cache import cache
        
        if not self.service.isdefined and self.service.needs_service_def == True:
            #log.debug('ServiceClient:  calling service definition load %s/%s' % (self.service.app_slug,self.service.name))
            self.service.load_definition(request_key=request)
        
        if request is None:
            request = self.service.name
        if self.service.format == 'xmlrpc':
            log.debug('about to create xmlrpc servicetransport')
            self.transport = XmlRpcServiceTransport(request=request)
            self.transport.service = self.service
        url = self.service.get_url(request=request)
        self.response.url = url
        #print('About to call fetch_service url= %s' % (url))
        cache_key = self.cache_key(url=url)
        #log.debug('about to check cache for url=%s' % url)
        if http_method != "GET" or not self.check_cache(cache_key):
            #print('no cache found')
            self.response = self.transport.fetch(url,data=data,extra_headers=self.extra_headers,http_method=http_method)
            
            if self.response.success:
                if self.service.format=='json' and self.response.data and len(self.response.data) > 3:
                    try:
                        self.response.json = json.loads(self.response.data)
                    except:
                        self.response.json = None
                    
                    #log.debug("creating json = %s" % self.response.json)
                #log.debug('success for service %s, %s' % (self.service.name,cache))
                #print self.response.data
                if cache is not None and self.use_cache:
                    #log.debug('setting cache key= %s, %s' % (cache_key,self.service.cache_time))
                    cache.set(cache_key,self.response,int(self.service.cache_time)) # TODO:  cachetime
            else:
                log.error('service error on fetch')
                #print('self.response.data = %s' % (self.response.data))
        #log.debug('returning from fetch %s' % (self.response))
        return self.response
    

def demisauce_ws_get(noun,resource_id,data={},cfgl={},format='html',extra_headers={},cache=True):
    return demisauce_ws(noun,resource_id,action='get',data=data,
                cfgl=cfgl,format=format,extra_headers=extra_headers,cache=cache)


def demisauce_ws(noun,resource_id,action=None,data={},cfgl={},
        format='json',extra_headers={},app='demisauce',http_method='GET',cache=True,cache_time=900):
    """
    Core web service get
    api/noun/id/action.format?apikey={yourkey}&q=query-or-search-parameters
    api/noun/id/selector.format
    api/noun/id.format?apikey=yourapikey
    
    examples:
        - api/service/email.json?apikey=myapikey
        - api/service/list.json?apikey=myapikey
        - api/email/welcomemessage?apikey=myapikey
        - api/person/1234.json?apikey
    
    Restful operations (create/read/update/delete)
        - (post=add/update, get=read, delete=delete)
    returns
    """
    client = ServiceClient(service=ServiceDefinition(
        name=noun,
        format=format,
        app_slug=app,
        cache=cache,
        cache_time=cache_time
    ))
    client.use_cache = cache
    client.extra_headers = extra_headers
    if action:
        resource_id = '%s/%s' % (resource_id,action)
    response = client.fetch_service(request=resource_id,data=data,http_method=http_method)
    return response


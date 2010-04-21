import urllib, urllib2, os, sys, logging
import string
import httpfetch
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # for GAE
        from django.utils import simplejson as json
import datetime
import hashlib
import warnings
import xmlrpclib
import re
import tornado
from tornado.options import options, define
from demisaucepy import xmlrpcreflector
import demisaucepy.cache_setup
from demisaucepy import cache

SUCCESS_STATUS = (200,201,204,304)

log = logging.getLogger("demisaucepy")

class RetrievalError(Exception):
    def __init__(self,message="There was an error retrieving this message"):
        self.message = message

def args_substitute(url_format,sub_dict):
    for k in sub_dict.keys():
        if sub_dict[k] is not None:
            url_format = url_format.replace('{%s}'%k,sub_dict[k])
    return url_format 

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
            #logging.debug("setting base url == %s" % options.demisauce_url)
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
            #if 'site' in jsondata and 'base_url' in jsondata['site']:
            #    self.base_url = jsondata['site']['base_url']
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
        self.success = True
        self.data = None
        self.body = None
        self.xmlrpc = None
        self.message = ''
        self.name = 'name'
        self.format = 'json'
        self.__xmlnode__ = None
        self.url = ''
        self.json = None
        self.status = 200
        self.was_cache = False
    
    def load(self,body=None):
        if body:
            self.body = body
        if self.format == 'json' and self.body:
            self.json = json.loads(self.body)
    
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
    
    def fetch(self,url,data={},extra_headers={},response=None,qs={},http_method='GET'):
        response = response or ServiceResponse()
        useragent = 'DemisaucePY/1.0'
        try: 
            #log.debug('httptransport getting url: %s' % (url))
            response.params = httpfetch.fetch(url, data=data,agent=useragent,extra_headers=extra_headers,http_method=http_method)
            response.status = response.params['status']
            response.url = url
            if 'data' in response.params:
                response.load(response.params['data'])
            if not response.status in SUCCESS_STATUS:
                response.success = False
        except urllib2.URLError, err:
            if err[0][0] == 10061:
                response.success = False
                log.error('No Server, refused connection = %s' % url)
                response.message = 'the remote server refused connection'
                        
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
        pass
    
    def authorize(self):
        pass
    
    def fetch_service(self):
        raise NotImplementedError
    
    def close(self):
        pass
    

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
    
    def delete_cache(self,url=None):
        if not url:
            url = self.service.get_url(request=request)
        cache_key = self.cache_key(url=url)
        cache.cache.delete(cache_key)
    
    def cache_key(self,url):
        if self._cache_key:
            return self._cache_key
        cache_key = url
        for key in self.extra_headers:
            cache_key += '%s:%s' % (key,self.extra_headers[key])
        cache_key = hashlib.md5(cache_key.lower()).hexdigest()
        self._cache_key = cache_key
        return cache_key
    
    def check_cache(self,cache_key):
        """Checks cache for this request"""
        #import demisaucepy.cache_setup
        #from demisaucepy.cache import cache
        
        if self.use_cache == False:
            return False
        if cache.cache == None:
            log.error('doesnt have cache configured')
            return False
        
        #log.debug('checking cache key=%s' % cache_key)
        cacheval = None
        #cache.delete(cache_key)
        cacheval = cache.cache.get(cache_key)
        if cacheval != None:
            log.debug('cache found for =url = %s, key = %s' % (self.response.url,cache_key))
            #self.response.data = cacheval.data
            self.response.load(cacheval)
            self.response.was_cache = True
            return True
        else:
            #log.debug('cache NOT found for = %s' % (cache_key))
            return False
    
    def fetch_service(self,request=None,data={},http_method='GET',qs={}):
        '''fetch the service, check cache, cache result'''
        #self.connect(request=request)
        #self.authorize()
        request = str(request)
        if not self.service.isdefined and self.service.needs_service_def == True:
            log.debug('ServiceClient:  calling service definition load %s/%s' % (self.service.app_slug,self.service.name))
            self.service.load_definition(request_key=request)
        
        if request is None:
            request = self.service.name
        if self.service.format == 'xmlrpc':
            #log.debug('about to create xmlrpc servicetransport %s' % request)
            self.transport = XmlRpcServiceTransport(request=request)
            self.transport.service = self.service
        url = self.service.get_url(request=request)
        self.response.url = url
        
        cache_key = self.cache_key(url=url)
        #log.debug('about to call check cache for url=%s' % url)
        if http_method != "GET" or not self.check_cache(cache_key):
            #log.debug('fetch_service method = %s, url= %s' % (http_method,url))
            if self.use_cache == False:
                url = '%s&cache=false' % url if url.find("?") > 0 else '%s?cache=false' % url 
            self.response = self.transport.fetch(url,data=data,response=self.response,extra_headers=self.extra_headers,http_method=http_method,qs=qs)
            
            if http_method == 'DELETE':
                #cache.cache.delete(cache_key)
                return self.response
            
            if self.response.success:
                if self.service.format=='json' and self.response.body and len(self.response.body) > 3:
                    try:
                        #log.debug("loaded json data = %s" % (self.response.body))
                        self.response.load()
                    except:
                        logging.error("error parsing json? %s" % self.response.body)
                        self.response.json = None
                
                if cache is not None and self.use_cache and self.response.status in SUCCESS_STATUS:
                    #log.debug('setting cache key= %s, %s' % (cache_key,self.service.cache_time))
                    cache.cache.set(cache_key,self.response.body,int(self.service.cache_time)) 
            else:
                pass
                #log.error('service error on fetch %s' % request)
        return self.response
    

import urllib, urllib2, os, sys, logging
import ConfigParser
import string
import openanything
import datetime
from xmlnode import XMLNode
from demisaucepy import cfg, logger
from demisaucepy.cache import cache
import hashlib
import warnings

log = logging.getLogger(__name__)


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

def UrlFormatter(url_format,sub_dict):
    for k in sub_dict.keys():
        if sub_dict[k] is not None:
            url_format = url_format.replace('{%s}'%k,sub_dict[k])
    return url_format 

class ServiceDefinition(object):
    """
    service definition for a remote service

    :name: name of remote service
    :format: format (json,xml,html,rss) of remote service
    :app_slug: url friendly name of app  (demisauce,phpdemo,djangodemo):  entered
        into web admin when signing up
    :method_url:  url part of this service (many services/app=base_url)
    :url_format:  a simple string substitution of any of available values
    :api_key: secret api key for service
    :data: dict of name/value pair's to be added to request  (get/post)
    :base_url:  base url of the "app" (each app has many services, 
        shared base_url) ex:  http://demisauce.demisauce.com
        note, NOT trailing slash
    """
    _service_keys = ['name']
    def __init__(self, name,format='xml', data={},app_slug='demisauce',
            base_url=None,api_key=None,local_key='id'):
        self.name = name
        self.format = format
        self.app_slug = app_slug
        self.cache = True
        self.url_format = "{base_url}/api/{format}/{service}/{key}?apikey={api_key}"
        self.data = data
        self.isdefined = False
        self.method_url = None
        self.service_registry = None
        self.api_key = api_key
        self.base_url = base_url
        if api_key == None:
            self.api_key = cfg.CFG['demisauce.apikey']
        if base_url == None:
            self.base_url = cfg.CFG['demisauce.url']
    
    def clone(self):
        """Create a clone of this service definition"""
        ns = ServiceDefinition(name=self.name)
        ns.format = self.format
        ns.app_slug = self.app_slug
        ns.data = self.data
        ns.isdefined = self.isdefined
        ns.api_key = self.api_key
        ns.base_url = self.base_url
        return ns
    
    def reload_cfg(self):
        if cfg and 'demisauce.url' in cfg.CFG:
            self.base_url = cfg.CFG['demisauce.url']
        if 'demisauce.apikey' in cfg.CFG:
            self.api_key = cfg.CFG['demisauce.apikey']
    
    def load_definition(self,request_key='demisauce/comment'):
        """
        The service is partially defined through demisauce
        web service, partly local declaration, rest of definition
        is loaded once at startup with this and cached as part of the 
        python in memory class definition
        """
        log.info('ServiceDefinition.load_definitin() %s:%s ' % (self.app_slug, request_key))
        self.reload_cfg()
        self.service_registry = self.clone()
        self.service_registry.name = 'service'
        client = ServiceClient(service=self.service_registry)
        #client.connect()
        #client.authorize()
        response = client.fetch_service(request=('%s/%s' % (self.app_slug, self.name)))
        # setup more service definition
        model = response.model
        self.isdefined = True
        if model and model.base_url:
            #print dir(model)
            self.base_url = model.base_url
            log.debug('setting base_url to%s for%s %s ' % (self.base_url, self.app_slug, self.name))
            if hasattr(model,'method_url') and model.method_url != 'None':
                self.method_url = model.method_url
            if model.url_format and model.url_format != 'None':
                self.url_format = model.url_format
            else:
                self.url_format = None
            
        else:
            log.debug('no base url on service definition get')
        
    
    def __str__(self):
        return 'na'

class ServiceResponse(object):
    def __init__(self,format='xml'):
        self.success = False
        self.data = None
        self.name = 'name'
        self.format = 'xml'
        self.__xmlnode__ = None
        self.url = ''
    
    def getxmlnode(self):
        if self.__xmlnode__ == None and self.data != None:
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
        else:
            return None
    
    model = property(getxmlnode)

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

class HttpServiceTransport(ServiceTransportBase):
    def connect(self):
        print 'in http service transport connect'
        pass
    
    def fetch(self,url,data={},extra_headers={},response=None):
        response = response or ServiceResponse()
        #print 'in http service transport fetch'
        useragent = 'DemisaucePY/1.0'
        try: 
            print url
            response.params = openanything.fetch(url, data=data,agent=useragent,extra_headers=extra_headers)
            #print item.params['status']
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
    def __init__(self,service,transport=None):
        self.service = service # ServiceDefinition
        self.transport = transport or HttpServiceTransport()
        self.transport.service = service
        self.extra_headers = {}
        self.use_cache = True
        self.request = 'service'
        self.response = ServiceResponse(format=service.format)
        self._cache_key = None
        log.debug('ServiceClient init %s' % (service.name))
    
    def get_url(self,request):
        if hasattr(self.service,'url_format') and self.service.url_format == None:
            # use service.method_url not url_format
            return '%s/%s' % (self.service.base_url,self.service.method_url)
        else:
            d = {}
            try:
                d = {"base_url":self.service.base_url,
                    "format":self.service.format,
                    "service":self.service.name,
                    "method_url":self.service.method_url,
                    "key":request,
                    "app_slug":self.service.app_slug,
                    "api_key":self.service.api_key}
            except AttributeError, e:
                raise RetrievalError('Attribute URL problems')
            
            return UrlFormatter(self.service.url_format, d)
    
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
        print 'md5cachekey = %s' % (cache_key)
        self._cache_key = cache_key
        return cache_key
    
    def check_cache(self,cache_key):
        """
        """
        if self.use_cache == False:
            return False
        
        log.debug('checking cache key=%s' % cache_key)
        cacheval = None
        #cache.delete(cache_key)
        cacheval = cache.get(cache_key)
        if cacheval != None:
            log.debug('cache found for = %s' % (cache_key))
            self.response.data = cacheval.data
            self.response.success = True
            return True
        else:
            log.debug('cache NOT found for = %s' % (cache_key))
            return False
    
    def fetch_service(self,request='',data={}):
        #self.connect(request=request)
        #self.authorize()
        url = self.get_url(request=request)
        cache_key = self.cache_key(url=url)
        if not self.check_cache(cache_key):
            self.response = self.transport.fetch(url,data=data,extra_headers=self.extra_headers)
            if self.response.success:
                log.debug('success for service %s' % (self.service.name))
                #print self.response.data
                cache.set(cache_key,self.response)
            else:
                log.error('service error on fetch')
                print self.response.data
        return self.response
    

def demisauce_ws_get(method,resource_id,data={},cfgl={},format='html',extra_headers={}):
    return demisauce_ws(method,resource_id,verb='get',data=data,
                cfgl=cfgl,format=format,extra_headers=extra_headers)


def demisauce_ws(method,resource_id,verb='get',data={},cfgl={},format='html',extra_headers={},app='demisauce'):
    """
    Core web service get
    api/format/method/rid?queryparams
    
    examples:
        - api/html/cms/about/demisauce?apikey=myapikey
        - api/xml/email/welcomemessage?apikey=myapikey
        - api/xml/cms/about/demisauce?apikey=myapikey
        - api/json/cms/about/demisauce?apikey=myapikey
    
    Restful operations (create/read/update/delete)
        - api/xml/person/uniqueid?apikey=myapikey  
                (post=add/update, get=read, delete=delete)
    returns
    """
    service = ServiceDefinition(
        name=method,
        format=format,
        app_slug=app
    )
    client = ServiceClient(service=service)
    if not service.isdefined:
        log.debug('demisauce_ws.load_definition  %s/%s' % (service.app_slug,service.name))
        service.load_definition(request_key=service.name)
    client.extra_headers = extra_headers
    response = client.fetch_service(request=resource_id,data=data)
    return response


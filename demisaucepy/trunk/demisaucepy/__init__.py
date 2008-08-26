import urllib, urllib2, os, sys, logging
import ConfigParser
import string
import openanything
import datetime
from xmlnode import XMLNode
from demisaucepy import cfg
from demisaucepy.cache import cache
import hashlib
import warnings

log = logging.getLogger(__name__)

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

class ServiceDefinition(object):
    """
    service definition
    """
    def __init__(self, method,format='xml', data={},app='demisauce',base_url=None,api_key=None):
        self.method = method
        self.format = format
        self.app = app
        self.cache = True
        self.api_version = 'api'
        self.url_format = "{base_url}/api/{format}/{service}/{key}?apikey={api_key}"
        self.data = data
        self.isdefined = False
        self.service_url = None
        self.service_registry = None
        if api_key == None:
            self.api_key = cfg.CFG['demisauce.apikey']
        if base_url == None:
            self.base_url = cfg.CFG['demisauce.url']
    
    def clone(self):
        """Create a clone of this service definition"""
        ns = ServiceDefinition(method=self.method)
        ns.format = self.format
        ns.app = self.app
        ns.api_version = self.api_version
        ns.data = self.data
        ns.isdefined = self.isdefined
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
        print 'service %s:%s load_definition' % (self.app, request_key)
        self.service_registry = self.clone()
        self.service_registry.method = 'service'
        client = ServiceClient(service=self.service_registry)
        #client.connect()
        #client.authorize()
        key = '%s/%s' % (self.app, self.method)
        response = client.fetch_service(request=key)
        # setup more service definition
        model = response.model
        self.isdefined = True
        print 'updating property definitions for service %s' % self.method
        if model and model.base_url:
            #print dir(model)
            self.base_url = model.base_url
            print 'base_url now = %s' % self.base_url
            if model.url and model.url != 'None':
                self.service_url = model.url
            if model.url_format and model.url_format != 'None':
                self.url_format = model.url_format
            else:
                self.url_format = None
            
        else:
            print 'nope, no model or no base_url anyway'
            print response.data
    

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
            """    
            if self.__xmlnode__:
                    if self.__xmlnode__._xmlhash:
                        print 'len xmlnode=%s' % len(self.__xmlnode__._xmlhash.keys()) 
                        # if only one, thats undoubtedly it
            else:
                print self.data
            """
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
        print 'in http service transport fetch'
        useragent = 'DemisaucePY/1.0'
        try: 
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
                print 'error in demisauce_fetch'
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
        print 'ServiceClient init %s' % (service.method)
        self.service = service # ServiceDefinition
        self.transport = transport or HttpServiceTransport()
        self.transport.service = service
        self.extra_headers = {}
        self.request = 'service'
        self.response = ServiceResponse(format=service.format)
        self._cache_key = None
        print 'finished SErviceClient init'
    
    def get_url(self,request):
        #TODO get rid of these 3 lines
        print self.service.url_format
        url_val = '%s/%s/%s/%s/%s?apikey=%s' % (self.service.base_url,
            self.service.api_version,self.service.format,
            self.service.method,request, self.service.api_key)
        if self.service.url_format == None:
            # use service.url not url_format
            print 'not url_format'
            return '%s/%s' % (self.service.base_url,self.service.service_url)
        else:
            url_val = self.service.url_format
            d = {"base_url":self.service.base_url,
                "format":self.service.format,
                "service":self.service.method,
                "key":request,
                "api_key":self.service.api_key}
            for k in d.keys():
                url_val = url_val.replace('{%s}'%k,d[k])
            return url_val #.replace('{','').replace('}','')
    
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
        #print 'checking cache key=%s' % cache_key
        cacheval = None
        cache.delete(cache_key)
        cacheval = cache.get(cache_key)
        #print 'cache val = %s' % (cacheval)
        if cacheval != None:
            print 'cache found for = %s' % (cache_key)
            self.response.data = cacheval.data
            self.response.success = True
            return True
        else:
            print 'cache NOT found for = %s' % (cache_key)
            return False
    
    def fetch_service(self,request=''):
        print 'top fetch'
        #self.connect(request=request)
        #self.authorize()
        url = self.get_url(request=request)
        print 'ServiceClient.fetch_service: get url, checking cache first %s' % (url)
        cache_key = self.cache_key(url=url)
        if not self.check_cache(cache_key):
            self.response = self.transport.fetch(url)
            if self.response.success:
                print 'was success, setting cache'
                #print self.response.data
                cache.set(cache_key,self.response)
            else:
                print'233 ServiceClient failure'
                print self.response.data
        return self.response
    


#MARKED for deprecation below this
class Dsws(object):
    """
    Container class for return from web service calls
    """
    def __init__(self, method,resource_id,format, **kwargs):
        self.success = False
        self.method = method
        self.format = format
        self.rid = resource_id
        self.api_key = cfg.CFG['demisauce.apikey']
        self.service_url = cfg.CFG['demisauce.url']
        #self.url2 = '%s/api/%s/%s/%s?apikey=%s' % (cfg.CFG['demisauce.url'],format,
        #                method,resource_id, cfg.CFG['demisauce.apikey'])
        self.data = None
        self.__xmlnode__ = None
        warnings.warn("Dsws is deprecated, use ServiceClient")
    
    def get_url(self):
        url = '%s/api/%s/%s/%s?apikey=%s' % (self.service_url,self.format,
                        self.method,self.rid, self.api_key)
        return url
    url = property(get_url)
    
    def get_from_cache(self):
        pass
    
    def getxmlnode(self):
        if self.__xmlnode__ == None:
            # probably need to verify we can parse this?
            self.__xmlnode__ = XMLNode(self.data)
        return self.__xmlnode__
    xml_node = property(getxmlnode)


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
    warnings.warn('demisauce_ws is depricated, use ServiceClient/ServiceHandler')
    item = Dsws(method,resource_id,format)
    useragent = 'DemisaucePY/1.0'
    try: 
        log.debug('url = %s, headers=%s' % (item.url, extra_headers))
        print item.url
        keyurl = item.url
        #TODO:  allow non vary by headers?
        for key in extra_headers:
            keyurl += '%s:%s' % (key,extra_headers[key])
        key = hashlib.md5(keyurl.lower()).hexdigest()
        print 'md5cachekey = %s' % (key)
        cacheval = None
        #cache.delete(key)
        cacheval = cache.get(key)
        #print 'cache val = %s' % (cacheval)
        if cacheval != None:
            #print 'cache item.data = %s' % (cacheval.data)
            return cacheval
        else:
            item.params = openanything.fetch(item.url, data=data,agent=useragent,extra_headers=extra_headers)
            #print item.params['status']
            if item.params['status'] == 500:
                item.message = 'there was an error on the demisauce server, \
                        no content was returned'
                log.error('500 = %s' % item.url)
            elif item.params['status'] == 404:
                item.message = 'not found'
                log.debug('404 = %s' % item.url)
            elif item.params['status'] == 401:
                item.message = 'Invalid API Key'
                log.debug('401 = %s' % item.url)
            else:
                item.data = item.params['data']
                item.success = True
                item.message = 'success'
            #TODO:  don't cache errors?
            cache.set(key,item)
            print 'adding item to cache key=%s, ' % (key)
            return item
    except urllib2.URLError, err:
        if err[0][0] == 10061:
            print 'error in demisauce_ws'
            log.debug('No Server = %s' % item.url)
            # connection refused
            item.message = 'the remote server didn\'t respond at \
                    <a href=\"%s\">%s</a> ' % (item.url,item.url)
    
    return item


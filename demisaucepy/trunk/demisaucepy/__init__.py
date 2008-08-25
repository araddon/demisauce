import urllib, urllib2, os, sys, logging
import ConfigParser
import string
import openanything
import datetime
from xmlnode import XMLNode
from demisaucepy import cfg
from demisaucepy.cache import cache
import hashlib

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

class HttpServiceClient(object):
    """
    Container class for return from web service calls
    demisauce_fetch(self.name,self.key,data={'views':service_handle},
                format=self.format,extra_headers=self.extra_headers,app=self.app)
    """
    def __init__(self, method,key,format='xml', data={},extra_headers={},app='demisauce'):
        self.success = False
        self.method = method
        self.key = key
        self.format = format
        self.app = app
        self.extra_headers = extra_headers
        self.data = data
        self.api_key = cfg.CFG['demisauce.apikey']
        self.service_url = cfg.CFG['demisauce.url']
        self.data = None
        self.__xmlnode__ = None
    
    def get_url(self):
        url_val = '%s/api/%s/%s/%s?apikey=%s' % (self.service_url,self.format,
                        self.method,self.key, self.api_key)
        return url_val
    url = property(get_url)

    def get_from_cache(self):
        pass
    
    def fetch(self,url):
        useragent = 'DemisaucePY/1.0'
        try: 
            self.params = openanything.fetch(url, data=self.data,agent=useragent,extra_headers=self.extra_headers)
            #print item.params['status']
            if self.params['status'] == 500:
                self.message = 'there was an error on the demisauce server, \
                        no content was returned'
                log.error('500 = %s' % item.url)
            elif self.params['status'] == 404:
                self.message = 'not found'
                log.debug('404 = %s' % item.url)
            elif self.params['status'] == 401:
                self.message = 'Invalid API Key'
                log.debug('401 = %s' % item.url)
            else:
                self.data = self.params['data']
                self.success = True
                self.message = 'success'
        except urllib2.URLError, err:
            if err[0][0] == 10061:
                print 'error in demisauce_fetch'
                log.debug('No Server = %s' % url)
                # connection refused
                self.message = 'the remote server didn\'t respond at \
                        <a href=\"%s\">%s</a> ' % (url,url)
        
    
    def retrieve(self):
        url = self.url
        print 'getting url %s' % url
        log.debug('url = %s, headers=%s' % (url, self.extra_headers))
        print 'httpclient.retrieve url=%s' % url
        keyurl = url
        #TODO:  allow non vary by headers?
        for key in self.extra_headers:
            keyurl += '%s:%s' % (key,self.extra_headers[key])
        key = hashlib.md5(keyurl.lower()).hexdigest()
        print 'md5cachekey = %s' % (key)
        cacheval = None
        #cache.delete(key)
        cacheval = cache.get(key)
        #print 'cache val = %s' % (cacheval)
        if cacheval != None:
            #print 'cache item.data = %s' % (cacheval.data)
            self.data = cacheval.data
            self.success = True
        else:
            self.fetch(url)
            cache.set(key,self)
            print 'adding item to cache key=%s, ' % (key)
    
    def getxmlnode(self):
        if self.__xmlnode__ == None:
            # probably need to verify we can parse this?
            self.__xmlnode__ = XMLNode(self.data)
        return self.__xmlnode__

    xml_node = property(getxmlnode)

class ServiceHandler(object):
    def __init__(self,name,key,extra_headers={},format='view',app='demisauce'):
        self.name = name
        self.key = key
        self.extra_headers = extra_headers
        self.format = format
        self.app = app
    
    def __getattr__(self,service_handle=''):
        """Allows for view's unknown to this code base to be retrieved::

            entry.comments.views.summary
            entry.comments.views.detailed
            entry.comments.views.recent

            entry.comments.model

        Would all be valid (summary,detailed,recent)
        """
        log.debug('calling dsws %s' % service_handle)
        client = HttpServiceClient(self.name,self.key,data={'views':service_handle},
                    format=self.format,extra_headers=self.extra_headers,app=self.app)
        
        client.retrieve()
        if client.success == True and self.format == 'view':
            return client.data
        elif client.success == True and self.format == 'xml':
            return client.xml_node._xmlhash[self.name]
        else:
            print client.params['status']
            return []

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


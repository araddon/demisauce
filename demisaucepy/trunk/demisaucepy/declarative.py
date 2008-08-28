"""
This is a set of base meta class definition for a declarative
definition builder to add demisauce capability to remote systems.  

Events and Aggregations::
    
    class AthleticPerson(Person):
        __demisaucetype__ = 'athlete'
        publish_to = DemisaucePublications('person_delete')
        subscribe_to = DemisauceEvents('person_add',filter=Person,newuser_setup)
        comments = has_many('comments',local_key='id',
                    lazy=True,views=['summary','list','details'])
        
        def newuser_setup(entity):
            # your logic here
            
"""
import datetime, urllib, logging, threading, time, urlparse
from demisaucepy import cfg
from demisaucepy.cache import cache
from demisaucepy import demisauce_ws, hash_email, \
    ServiceDefinition, ServiceClient, RetrievalError, \
    UrlFormatter


DSDEBUG = False
_modeltype_map = {}
log = logging.getLogger(__name__)

class MappingError(Exception):
    """what?"""

class ConfigurationError(Exception):
    """Raised when the config key is improperly configured."""

class DuplicateMapping(Exception):
    """Raised when the same demisauce entity type is declared for 
    a class or inheritied class with the same name."""



class ServiceHandler(object):
    def __init__(self,model_instance,service,local_key='id',this_app='',
        extra_headers={},key_format=''):
        self.service = service
        self.model_instance = model_instance
        self.extra_headers = extra_headers
        self.local_key = local_key
        self.this_app_slug = this_app
        self.is_loaded = False
        self.key_format = key_format
        self.lazy = True
        self.client = None
        self.previous_call = ''
    
    def get_service(self,service='views',format='view',data={}):
        self.service.format = format
        client = ServiceClient(service=self.service)
        client.extra_headers = self.extra_headers
        log.debug('about to fetch %s' % self.key())
        response = client.fetch_service(request=self.key())
        if response.success == True and self.service.format == 'view':
            #print response.data
            return response.data
        elif self.service.format == 'xml':
            return response
        else:
            print response.message
            return []
    
    def add_cookies(self,ckie_dict={}):
        if not 'Cookie' in self.extra_headers:
            val = ''
            for ck in ckie_dict:
                val += urllib.urlencode({ck:ckie_dict[ck]}) + '; '
            self.extra_headers['Cookie'] = val
    
    def key(self):
        #print 'making key %s' % self.key_format
        d = {"app_slug":self.this_app_slug,
            "class_name":self.model_instance.__class__.__name__,
            "local_key":str(getattr(self.model_instance,self.local_key))}
        return UrlFormatter(self.key_format, d)
    
    def __getattr__(self,get_what):
        #print 'in __getattr__ of servicehandler  %s' % (get_what)
        if self.lazy and not self.is_loaded:
            if not self.service.isdefined:
                log.debug('ServiceProperty.get_service:  calling service definition load %s/%s' % (self.service.app_slug,self.service.name))
                self.service.load_definition(request_key=self.service.name)
                self.is_loaded = True
        
        if get_what.lower() == 'model':
            if not get_what in self.__dict__:
                resp = self.get_service(service='model',format='xml')
                if resp.success:
                    model = resp.model
                    setattr(self,get_what,model)
                else:
                    return None
            return getattr(self,get_what)
        elif self.previous_call.lower() == 'views' and get_what != 'views':
            #print 'views:  prev=%s , get_what= %s' % (self.previous_call,get_what)
            if not get_what in self.__dict__:
                view_result = self.get_service(service='views',format='view',data={'views':get_what})
                setattr(self,get_what,view_result)
            self.previous_call = ''
            return getattr(self,get_what)
        elif self.previous_call.lower() == 'model':
            return getattr(self,'model')
        else:
            self.previous_call = get_what
        #print 'returning self for = %s' % get_what
        return self
    

class ServiceProperty(object):
    """
    An entity mapper for remote entities.   
    
    NOTE:  this is an instance per property and act's as a metaclass
    as it runs at initiation time NOT runtime, one instance per
    defined service property
    
    *construction parameters*
    :name: comments, person, email, poll, etc 
        (must be a demisauce entity type)
    :lazy: (true/false) optional, defaults to True
    :local_key: (optional, defaults to id) used for joins
    :app:  app provider (many dift service providers)
    """
    def __init__(self, name, local_key='id',format='xml',lazy=True,app="demisauce"):
        super(ServiceProperty, self).__init__()
        self.service = ServiceDefinition(
            name=name,
            format=format,
            app_slug=app
        )
        log.debug('init: setting service definition %s/%s, format=%s' % (app,name,format))
        #self.service.load_definition(request_key=name)
        self.name = name
        self.app_slug = app
        self.key_format = '{app_slug}/{class_name}/{local_key}'
        self.lazy = lazy
        self.this_app_slug = 'yourappname'
        self.islist = True
        self.local_key = local_key
        self.extra_headers = {}
        log.debug('ServiceProperty: service.name=%s, service.app=%s' % (self.service.name,self.service.app_slug))
    
    def reload_cfg(self):
        if cfg and 'demisauce.appname' in cfg.CFG:
            self.this_app_slug = cfg.CFG['demisauce.appname']
            print 'found app name %s' % self.this_app_slug
    
    def add_request(self,req_dict):
        if hasattr(threading.local(), 'ds_request'):
            local_req = getattr(threading.local(),'ds_request')
        else:
            local_req = {'cache':True}
        if 'cache' in req_dict and str(req_dict['cache']).lower() == 'false':
            local_req['cache'] = False
        
        setattr(threading.local(), 'ds_request', local_req)
    
    def add_cookies(self,ckie_dict={}):
        if not 'Cookie' in self.extra_headers:
            val = ''
            for ck in ckie_dict:
                val += urllib.urlencode({ck:ckie_dict[ck]}) + '; '
            self.extra_headers['Cookie'] = val
    
    def __get__(self, model_instance, model_class):
        """
        user is trying to access the declarative, if not an instance (Class Property)
        return this, else return the service handler for this mapped service
        
        about: http://docs.python.org/ref/descriptors.html
        """
        #print 'in __get__ %s, class=%s,  name=%s' %(model_instance,model_class,self._attr_name())
        if model_instance is None:
            return self
        
        if not hasattr(model_instance,self._attr_name()):
            self.reload_cfg()
            sh = ServiceHandler(model_instance=model_instance,service=self.service,
                    local_key=self.local_key,this_app=self.this_app_slug,key_format=self.key_format)
            sh.extra_headers = self.extra_headers
            setattr(model_instance, self._attr_name(),sh)
        return getattr(model_instance, self._attr_name())
    
    def __set__(self, model_instance, value):
        """not implemented"""
        raise NotImplementedError
        setattr(model_instance, self._attr_name(), value)
    
    def _attr_name(self):
        """internal name for demisauce entities"""
        return '_' + self._instance_name
    

class has_a(ServiceProperty):
    """Has a single mapped entity(service)"""
    def __init__(self, name,**kwargs):
        super(has_a, self).__init__(name,**kwargs)
        self.islist = False
        self.key_format = '{local_key}'
    

class has_many(ServiceProperty):
    """Has many"""
    def __init__(self, name,**kwargs):
        super(has_many, self).__init__(name,**kwargs)
        self.islist = True
    

class AggregatorMeta(type):
    """This is a metaclass that setup's the Entity class's
    at definition time with information necessary for ServiceProperty
    to use"""
    def __init__(cls, classname, bases, dict_):
        super(AggregatorMeta, cls).__init__(classname, bases, dict_)
        for attr_name in dict_.keys():
            attr = dict_[attr_name]
            if isinstance(attr, ServiceProperty):
                attr._instance_name = attr_name
    

def aggregator_callable(cls=object):
    """
    For use if you need to use inheritance
    """
    class InternalBase(cls):
        __metaclass__ = AggregatorMeta
    
    return InternalBase

Base = aggregator_callable()

class Aggregagtor(Base):
    def __init__(self,**kwargs):
        super(Aggregagtor, self).__init__()
    

        
class AggregateView(object):
    def __init__(self,meta,views=[]):
        self.views = meta.get_views(views)
    


if __name__ == "__main__":
    pass
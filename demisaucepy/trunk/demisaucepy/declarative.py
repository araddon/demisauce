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
import datetime
import urllib
import logging
import time
import urlparse
from demisaucepy import cfg
from demisaucepy.cache import cache
from demisaucepy import demisauce_ws, hash_email, \
    ServiceDefinition, HttpServiceClientOld


DSDEBUG = False
_modeltype_map = {}
log = logging.getLogger(__name__)

class RetrievalError(Exception):
    """No result?"""

class MappingError(Exception):
    """what?"""

class ConfigurationError(Exception):
    """Raised when the config key is improperly configured."""

class DuplicateMapping(Exception):
    """Raised when the same demisauce entity type is declared for 
    a class or inheritied class with the same name."""



# what to do w this?  attach to the instance?
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
        if service_handle in self.__dict__:
            return self.__dict__[service_handle]
        log.debug('calling HttpServiceClient %s' % service_handle)
        client = HttpServiceClientOld(self.name,self.key,data={'views':service_handle},
                    format=self.format,extra_headers=self.extra_headers,app=self.app)
        #self.__dict__['message'] = client.message
        client.retrieve()
        if client.success == True and self.format == 'view':
            return client.data
        elif client.success == True and self.format == 'xml':
            return client.xml_node._xmlhash[self.name]
        else:
            print client.message
            return []
    

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
            method=name,
            format='xml',
            app=app
        )
        key = '%s/%s' % (app,name)
        print 'in ServiceProperty before load %s' % (key)
        #self.service.load_definition(key=name)
        
        self.name = name
        self.app = app
        
        self.lazy = lazy
        self._loaded = False
        self.islist = True
        self.local_key = local_key
        self.local_key_val = None
        self._model_instance = None
        self.extra_headers = {}
        print 'ServiceProperty: service.method=%s, service.app=%s' % (self.service.method,self.service.app)
    
    def get_service(self,service='views',format='view'):
        if self.lazy and not self.is_loaded(service):
            if not self.service.isdefined:
                key = '%s/%s' % (self.app,self.name)
                print 'in ServiceProperty ServiceDefinition load %s' % (key)
                self.service.load_definition(request_key=self.name)
            eh = {}
            if self.extra_headers:
                eh = self.extra_headers
            service_handler = ServiceHandler(self.name,self.key(),extra_headers=eh,format=format)
            self.set_loaded(service,service_handler)
        else:
            service_handler = self.get_loaded(service)
        return service_handler
        #TODO:  handle error
        try:
            pass
        except AttributeError:
            return None
    
    views = property(get_service)
    def view(self,which_view=''):
        """docstring for view"""
        pass
    
    def key(self):
        return '/'.join([cfg.CFG['demisauce.appname'],self.entityname,str(self.local_key_val)])
    
    def add_cookies(self,ckie_dict={}):
        if not 'Cookie' in self.extra_headers:
            val = ''
            for ck in ckie_dict:
                val += urllib.urlencode({ck:ckie_dict[ck]}) + '; '
            self.extra_headers['Cookie'] = val
    
    def is_loaded(self,what='model'):
        """checks if this item is loaded"""
        loaded_key = 'loaded%s' % what
        if self._attr_name() in self._model_instance._ds_aggregate:
            if what in self._model_instance._ds_aggregate[self._attr_name()]:
                return True
        return False
    
    def get_loaded(self,what='model'):
        return self._model_instance._ds_aggregate[self._attr_name()][what]
    
    def set_loaded(self,what='model',value=None):
        self._model_instance._ds_aggregate[self._attr_name()][what] = value
    
    def get_model(self):
        """Returns the entity collection/item appropriate"""
        return self.get_service(service='model',format='xml').model
    
    model = property(get_model)
    
    """def get_model2(self):
        #Returns the entity collection/item appropriate
        res = self.get_service(service='model',format='xml').model
        def getxmlnode(self):
            if self.__xmlnode__ == None:
                # probably need to verify we can parse this?
                self.__xmlnode__ = XMLNode(self.data)
            return self.__xmlnode__

        xml_node = property(getxmlnode)
        return 
    
    model2 = property(get_model)"""
    def __get__(self, model_instance, model_class):
        """user is trying to access this as if its a property?"""
        print 'in __get__ %s, class=%s,  name=%s' %(model_instance,model_class,self.name)
        if model_instance is None:
            return self
        
        if not hasattr(model_instance,'_ds_aggregate'):
            setattr(model_instance, '_ds_aggregate', {})
        if not self._attr_name() in model_instance._ds_aggregate:
            model_instance._ds_aggregate[self._attr_name()] = {}
        self._model_instance = model_instance   #
        self.local_key_val = getattr(model_instance, self.local_key)
        return self
    
    def __set__(self, model_instance, value):
        """Sets the value for this property on the given model instance.
        
        See http://docs.python.org/ref/descriptors.html for a description of
        the arguments to this class and what they mean.
        """
        print 'in set attr %s' % (value)
        setattr(model_instance, self._attr_name(), value)
    
    def _attr_name(self):
        """internal name for demisauce entities"""
        return '_' + self.name
    

class has_a(ServiceProperty):
    """Has a single"""
    def __init__(self, name,**kwargs):
        super(has_a, self).__init__(name,**kwargs)
        self.islist = False
    
    def key(self):
        return str(self.local_key_val)
    

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
                attr.entityname = classname
    

def aggregator_callable(cls=object):
    """
    For use if you need to use inheritance
    """
    class InternalBase(cls):
        __metaclass__ = AggregatorMeta
        def __init__(self, **kwargs):
            pass
        
        @classmethod
        def kind(cls):
            """Returns the entity type"""
            return cls.__name__
    
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
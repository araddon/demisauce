"""
This is a set of base meta class definition for a declarative
definition builder to add demisauce capability to remote systems.  

Events and Aggregations::
    
    class AthleticPerson(Person):
        __demisaucetype__ = 'athlete'
        publish_to = DemisaucePublications('person_delete')
        subscribe_to = DemisauceEvents('person_add',filter=Person,newuser_setup)
        comments = has_many('activities',local_key='ds_id')
        
        def newuser_setup(entity):
            # your logic here
        
    
"""
import datetime, urllib, logging, threading, time, urlparse
from demisaucepy.cache import cache
from demisaucepy import demisauce_ws, hash_email
from demisaucepy.service import ServiceDefinition, ServiceClient, \
    RetrievalError, args_substitute


DSDEBUG = False
_modeltype_map = {}
log = logging.getLogger("demisaucepy")

class MappingError(Exception):
    """what?"""

class ConfigurationError(Exception):
    """Raised when the config key is improperly configured."""

class DuplicateMapping(Exception):
    """Raised when the same demisauce entity type is declared for 
    a class or inheritied class with the same name."""


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
    def __init__(self, obj_type, local_key='id'):
        super(ServiceProperty, self).__init__()
        cls_name = str(obj_type)
        cls_name = cls_name[cls_name.find('.')+1:cls_name.rfind('\'')].lower()
        self.name = cls_name
        log.debug('init: setting service definition declarative property %s' % (self.name))
        self.obj_type = obj_type
        self.islist = True
        self.local_key = local_key
    
    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self
        
        if not hasattr(model_instance,self._attr_name()):
            #self.reload_cfg()
            log.debug('getting declarative svc for %s' % (self._attr_name()))
            key = getattr(model_instance,self.local_key)
            svc = self.obj_type.GET(key)
            setattr(model_instance, self._attr_name(),svc)
            return svc
        return getattr(model_instance, self._attr_name())
    
    def _attr_name(self):
        """internal name for demisauce entities"""
        return '_' + self.name
    

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
    

def make_declarative(dict_):
    for attr_name in dict_.keys():
        attr = dict_[attr_name]
        if isinstance(attr, ServiceProperty):
            attr._instance_name = attr_name

class AggregatorMeta(type):
    """This is a metaclass that setup's the Entity class's
    at definition time with information necessary for ServiceProperty
    to use"""
    def __init__(cls, classname, bases, dict_):
        #log.info("in aggregator meta %s" % (classname))
        super(AggregatorMeta, cls).__init__(classname, bases, dict_)
        make_declarative(dict_)
    

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
    


if __name__ == "__main__":
    pass
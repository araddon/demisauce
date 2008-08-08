"""
This is a set of base meta class definition for a declarative
definition builder to add demisauce capability to remote systems.  

Events and Mappings::
    
    class AthleticPerson(Person):
        __demisaucetype__ = 'athlete'
        publish_to = DemisaucePublications('delete')
        subscribe_to = DemisauceEvents('add',filter=Person,newuser_setup)
        comments = DemisauceMapping('comments',local_key=id,
                    lazy=true,views=['summary','list','details'])
        def newuser_setup(entity):
            # your logic here
            
"""
import datetime
import logging
import time
import urlparse
from demisaucepy import demisauce_ws, hash_email, \
    Comment, Person as DemisaucePerson
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

class Aggregate(object):
    """
    An entity mapper for remote entities
    *construction parameters*
    :name: comments, person, email, poll, etc 
        (must be a demisauce entity type)
    :lazy: (true/false) optional, defaults to True
    :local_key: (optional, defaults to id) used for joins
    """
    def __init__(self, name='',lazy=True,local_key="id"):
        super(Aggregate, self).__init__()
        self.name = name
        self.lazy = lazy
        self._loaded = False
        self.islist = True
        self.local_key = local_key
        self.local_key_val = None
    
    def get_views(self,views=[]):
        try:
            print '58 about to get views %s' % (self.name)
            key = self.local_key_val
            #TODO:  which view's?   all or just requested?
            dsitem = demisauce_ws(self.name,key,format='view',data={'views':views})
            if dsitem.success == True:
                return dsitem.xml_node._xmlhash[self.name]
            else:
                raise RetrievalError('no result %s' % dsitem.data)
            setattr(model_instance, self._attr_name(), [])
            return getattr(model_instance, self._attr_name())
        except AttributeError:
            return None
    
    views = property(get_views)
    
    def get_model(self):
        """Returns the entity collection/item appropriate
        """

        try:
            # lazy load it?
            if self.lazy and not self._loaded:
                print '82 about to get model lazy loaded %s' % (self.name)
                print 'local_key = %s' % self.local_key
                key = self.local_key_val
                print 'key = %s' % key
                dsitem = demisauce_ws(self.name,key,format='xml')
                if dsitem.success == True:
                    #setattr(model_instance, self._attr_name(), dsitem.xml_node._xmlhash[self.name])
                    setattr(self, self._attr_name(), dsitem.xml_node._xmlhash[self.name])
                    self._loaded = True
                else:
                    setattr(self, self._attr_name(), [])
                    raise RetrievalError('no result %s' % dsitem.data)

            #return getattr(model_instance, self._attr_name())
            return getattr(self, self._attr_name())
        except AttributeError:
            return None
    
    model = property(get_model)
    
    def __get__(self, model_instance, model_class):
        """Returns the entity collection/item appropriate
        
        See http://docs.python.org/ref/descriptors.html for more about descriptors
        or this article:
        http://pythonisito.blogspot.com/2008/07/restfulness-in-turbogears.html
        """
        self.local_key_val = getattr(model_instance, self.local_key)
        return self
        if model_instance is None:
            return self
        
        try:
            # lazy load it?
            if self.lazy and not self._loaded:
                print '109 about to get lazy loaded %s' % (self.name)
                print 'local_key = %s' % self.local_key
                key = getattr(model_instance, self.local_key)
                print 'key = %s' % key
                dsitem = demisauce_ws(self.name,key,format='xml')
                if dsitem.success == True:
                    setattr(model_instance, self._attr_name(), dsitem.xml_node._xmlhash[self.name])
                    self._loaded = True
                else:
                    setattr(model_instance, self._attr_name(), [])
                    raise RetrievalError('no result %s' % dsitem.data)
            
            return getattr(model_instance, self._attr_name())
        except AttributeError:
            return None
    
    def __set__(self, model_instance, value):
        """Sets the value for this property on the given model instance.
        
        See http://docs.python.org/ref/descriptors.html for a description of
        the arguments to this class and what they mean.
        """
        value = self.validate(value)
        setattr(model_instance, self._attr_name(), value)
    
    def _attr_name(self):
        """internal name for demisauce entities"""
        return '_' + self.name
    
    def __ds_mapping_config__(self, model_class, model_name):
        """Configure mapping, relating a demisauce remote
        entity model to its local python class.  The local python
        model name forms part of the type
        
        Args:
        model_class: Local model which remote demisauce entity model will belong to
        model_name: Name of model
        """
        self.model_name = model_name
        self.model_class = model_class
    

class has_a(Aggregate):
    """Has a single"""
    def __init__(self, name,**kwargs):
        super(has_a, self).__init__(name,**kwargs)
        self.islist = False
    

class has_many(Aggregate):
    """Has many"""
    def __init__(self, name,**kwargs):
        super(has_many, self).__init__(name,kwargs)
        self.islist = True
    

class AggregatorMeta(type):
    def __init__(cls, classname, bases, dict_):
        if DSDEBUG:
            print 'in ds AggregatorMeta init classname = %s \n \
            bases = %s \n \
            dict_ = %s \n \
            cls = %s' % (classname, bases, dict_,cls)
        
        super(AggregatorMeta, cls).__init__(classname, bases, dict_)
        
        cls._dsmappings = {}
        defined = set()
        for base in bases:
            if hasattr(base, '_dsmappings'):
                dsmappings_keys = base._dsmappings.keys()
                duplicate_mappings = defined.intersection(dsmappings_keys)
                if duplicate_mappings:
                    raise DuplicateMapping(
                      'Duplicate demisauce models in base class %s already defined: %s' %
                      (base.__name__, list(duplicate_mappings)))
                defined.update(dsmappings_keys)
                cls._dsmappings.update(base._dsmappings)
        
        for attr_name in dict_.keys():
            attr = dict_[attr_name]
            if isinstance(attr, Aggregate):
                if attr_name in defined:
                    raise DuplicateMapping('Duplicate mapping: %s' % attr_name)
                defined.add(attr_name)
                cls._dsmappings[attr_name] = attr
                attr.__ds_mapping_config__(cls, attr_name)
        
        #_modeltype_map[cls.kind()] = cls
        
        if not hasattr(cls, 'publishes_to'):
            cls._publishes_to = []
        else:
            cls._publishes_to.append(cls)
            
        if not hasattr(cls, 'subscribes_to'):
            cls._subscribes_to = []
        else:
            cls._subscribes_to.append(cls)
        
    

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
        
        @classmethod
        def dsmappings(cls):
            """Returns a info"""
            return dict(cls._dsmappings)
        
    
    return InternalBase

Base = aggregator_callable()

class Aggregagtor(Base):
    def __init__(self,**kwargs):
        super(Aggregagtor, self).__init__()
    

        
class AggregateView(object):
    def __init__(self,meta,views=[]):
        # use metaclass info
        self.views = meta.get_views(views)
    


if __name__ == "__main__":
    print 'hello'
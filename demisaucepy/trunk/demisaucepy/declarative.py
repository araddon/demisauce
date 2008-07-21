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
DSDEBUG = False
_modeltype_map = {}
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
    name = comments, person, email, poll, etc
    local_key (optional, defaults to id) used for joins
    lazy = (true/false) optional, defaults to True
    """
    def __init__(self, name,lazy=True,local_key="id"):
        super(Aggregate, self).__init__()
        self.name = name
    
    def __get__(self, model_instance, model_class):
        """Returns the entity collection/item appropriate
        
        See http://docs.python.org/ref/descriptors.html for more about descriptors
        or this article:
        http://pythonisito.blogspot.com/2008/07/restfulness-in-turbogears.html
        """
        print 'in __get__  %s' % (model_instance)
        if model_instance is None:
            return self

        try:
            return getattr(model_instance, self._attr_name())
        except AttributeError:
            return None
    
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
        self.model_class = model_class
        if self.name is None:
            self.name = '_%s' % model_name
    


class AggregatorMeta(type):
    def __init__(cls, classname, bases, dict_):
        if DSDEBUG:
            print 'in ds DemisauceDeclarativeMeta init classname = %s \n \
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
        
        _modeltype_map[cls.kind()] = cls
        
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
            print 'in ds_aggregator_callable Base inner cls=%s' % cls
        
        @classmethod
        def kind(cls):
            """Returns the entity type"""
            return cls.__name__
        
        @classmethod
        def dsmappings(cls):
            """Returns a info"""
            return dict(cls._dsmappings)
        
    
    return InternalBase

class YourCustomClass(object):
    def __init__(self, arg):
        super(YourCustomClass, self).__init__()
        self.arg = arg
    

AggregatorCallableCustomInheritanceTest = aggregator_callable(YourCustomClass)
Base = aggregator_callable()
class Aggregagtor(Base):
    #__metaclass__ = AggregatorMeta
    pass


class Person(Aggregagtor):
    """
    Demo person class, showing direct inheritance implementation
    of Demisauce Aggregate Functions
    """
    comments = Aggregate('comments',lazy=True)
    def __init__(self, displayname, email):
        super(Person, self).__init__()
        self.displayname = displayname
        self.email = email
    
class TestCustomInheritance(AggregatorCallableCustomInheritanceTest):
    def __init__(self, arg):
        super(TestCustomInheritance, self).__init__()
        self.arg = arg


if __name__ == "__main__":
    print 'before ()'
    t2 = Person('aaron','email@email.com')
    t2.att2 = 'att2'
    t3 = TestCustomInheritance('myarg')
    t3.fake = 'good'
    print t2.comments
    assert t2.comments

import logging
from pylons import c, cache, config, g, request, response, session
import simplejson

import demisauce.model as model
from demisauce.model import mapping, meta
from demisauce.model.person import Person

log = logging.getLogger(__name__)
"""
ok, overall design:

have a controller "register" a filter (by name)
the filter will have known methods (duck typing) that the filtermanager
will be able to call to "implement" a filter.  So, the "Filter" would 
be per filterable

??  how to implement multiple filters?   return the qry and allow futher filtering
to work on it?

filter group's?  ie, everything within a group would share the same base SqlAlchemy selectable from statement?
or, is there a way to do it dynamically?  add in a "from" 
"""
class Filter(object):
    """
    """
    def __init__(self,**kwargs):
        self.name = 'default'
        self._dict = {
            'name':'default',
            'value':'filtervalue',
            'offset':0,
            'count':0
        }
        self._load(self._dict)
        self._load(kwargs)
    
    def _load(self,dict):
        for a in kwargs:
            setattr(self,a,kwargs[a])
    

class FilterList(object):
    """
    FilterList is a tool for storing a memory using non 
    stateless (server side, cookie, memcached etc) for persisting
    a filter against a data set.
    example::
    
        def __before__(self):
            SecureController.__before__(self)
            self.helpfilter = self.filters['helpadmin']
    """
    def __init__(self,**kwargs):
        self.filters = {}
        self.context = ''
        self.load_filters()
    
    def add_param(self,name,val):
        fltr = self[self.context]
        if name in fltr:
            fltr[name] = val
        else:
            fltr[name] = val
        
        self.new(context=self.context,filter=fltr)
    
    def new(self,context='default',filter='{name:"bytag",value:"python"}'):
        if context in self.filters:
            self.filters[context] = filter
        else:
            self.filters[context] = filter
        self.context = context
        self.save()
    
    def current(self):
        """Return filter for current context"""
        return self[self.context]
    
    def get_filter(self):
        # use context to load filter
        return self[self.context]
    
    def save(self):
        
        """save to persistent store"""
        if len(self.filters) > 0:
            session['filters'] = self.filters
            session.save()
    
    def __getitem__(self, context):
        """Indexor to find a filter"""
        if context in self.filters:
            return self.filters[context]
        return None
    
    def load_filters(self):
        """filters are persistent containers for 
            filtering data across page views wout using
            stateless info"""
        if 'filters' in session:
            self.filters = session['filters']
        #elif 'filters' in request.cookies:
        #    self.filters = request.cookies['filters'].lower().split(',')
        
        if self.filters == None:
            self.filters = {}
        
    

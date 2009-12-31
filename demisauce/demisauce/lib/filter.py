import logging
import json

#import demisauce.model as model
#from demisauce.model import mapping, meta
#from demisauce.model.user import Person

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
    :context:  Each filter only applies to a "context" which is
        a (portion/aspect of the web site) such as the new help tickets
         page (filter by recent, filter by complete, assigned)
    :name:  name of this specific filter(for context) (recent,complete,assigned)
    :value: value of filter
    :offset:   for paging
    :clauses:  dictionary of clauses (filters, orders, etc, )
    :count: for storing # in this filtered set
    :site_id:  site_id for filtering
    """
    def __init__(self,**kwargs):
        self.context = 'comments'
        self.name = 'default'
        self.site_id = 0
        self.count = 0 # indicates newness
        self.offset = 0
        self.value = 'filtervalue'
        self.clauses = {}
        self._load(kwargs)
        self.qry = None
    
    def _load(self,kwargs):
        for a in kwargs:
            if hasattr(self,a):
                setattr(self,a,kwargs[a])
    
    def __str__(self):
        return "{context:'%s',name:'%s',value:'%s',clauses:'%s'}" % (self.context,self.name,self.value,self.clauses)
    
    def finish(self,offset=0,limit=0,safilter=None):
        for clause in self.clauses.keys():
            filter_function = getattr(self, "filterby_%s" % clause)
            filter_function(self.clauses[clause])
            print self.clauses[clause]
            
        q = self.qry
        
        self.count = q.count()# ?? persist once per?
        if self.offset == 0:
            #self.count = q.count()
            self.offset = offset
            q = self.qry.limit(limit)
        else:
            self.offset += offset
            if self.offset > self.count:
                return None
            else:
                q = self.qry.limit(limit).offset(self.offset-1)
        
        self.qry = None
        return q
    

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
    def __init__(self,context='none',site_id=0,cache=None,person_id=0):
        self.filters = {}
        self.context = context
        self.site_id = site_id
        self.person_id = person_id
        self.load_filters(cache=cache)
    
    def set(self,filter=None,cache=None):
        if not filter == None:
            filter.site_id = self.site_id
            self.filters[filter.context] = filter
            #print 'setting filter %s' % (filter)
            self.context = filter.context
            self.save(cache=cache)
    
    def current(self):
        """Return filter for current context"""
        return self.__getitem__(self.context)
    
    @property
    def key(self):
        return "filters-personid-%s" % self.person_id
    
    def save(self,cache=None):
        
        """save to persistent store"""
        if len(self.filters) > 0:
            cache.set(self.key,self.filters)
    
    def __getitem__(self, context):
        """Indexor to find a filter"""
        logging.debug("in __getitem__ filters, context = %s, filters=%s" % (context,self.filters))
        if type(context) == int and context == 0:
            raise Exception("what the hell")
        if context in self.filters:
            return self.filters[context]
        return None
    
    def load_filters(self,cache=None):
        """filters are persistent containers for 
            filtering data across page views wout using
            stateless info"""
        self.filters = cache.get(self.key)
        if self.filters == None:
            self.filters = {}
        
    

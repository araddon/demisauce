import logging
from pylons import c, cache, config, g, request, response, session
import simplejson

from demisauce.lib import JsonSerializeable
#import demisauce.model as model
#from demisauce.model import mapping, meta
#from demisauce.model.person import Person

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
class Filter(JsonSerializeable):
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
    def __init__(self,context='none',site_id=0):
        self.filters = {}
        self.context = context
        self.site_id = site_id
        self.load_filters()
    
    def set(self,filter=None):
        if not filter == None:
            filter.site_id = self.site_id
            self.filters[filter.context] = filter
            #print 'setting filter %s' % (filter)
            self.context = filter.context
            self.save()
    
    def current(self):
        """Return filter for current context"""
        return self.__getitem__(self.context)
    
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
        
    

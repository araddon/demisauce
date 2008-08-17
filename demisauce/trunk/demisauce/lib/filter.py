import logging
from pylons import c, cache, config, g, request, response, session
import simplejson

import demisauce.model as model
from demisauce.model import mapping, meta
from demisauce.model.person import Person

log = logging.getLogger(__name__)

class Filter(object):
    """
    Filter is a tool for storing a memory using non 
    stateless (server side, cookie, memcached etc) for persisting
    a filter against a data set.
    example::
    
    
        def __before__(self):
            SecureController.__before__(self)
            self.helpfilter = self.filters['helpadmin']
            if self.helpfilter == None:
                self.helpfilter = self.filters.new('helpadmin',{name:"new",value:""})
        
        def yourcontrolleraction(self,id=''):
            filter = self.filters['helpadmin']
            c.help_tickets = 
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
        
    def get_filter(self):
        # use context to load filter
        return self[self.context]
    
    def save(self):
        
        """save to persistent store"""
        if len(self.filters) > 0:
            session['filters'] = self.filters
            session.save()
    
    def __getitem__(self, context):
        """Indexor to find current filter"""
        self.context = context
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
        
    

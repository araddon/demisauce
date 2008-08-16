"""Filter is a tool for storing a memory using non 
stateless (server side, cookie, memcached etc) for persisting
a filter against a data set.
"""
import logging
from pylons import c, cache, config, g, request, response, session

import demisauce.model as model
from demisauce.model import mapping, meta
from demisauce.model.person import Person
import tempita

log = logging.getLogger(__name__)

class Filter(object):
    def __init__(self,**kwargs):
        pass
    
    def save(self,name):
        """docstring for save"""
        pass
    
    def __getitem__(self, name):
        """
        """
        return self
    
    def get_filters(self,name=None):
        """filters are persistent containers for 
            filtering data across page views wout using
            stateless info"""
        filters = None
        if 'filters' in session and type(session['filters']) == list:
            filters = session['filters']
        elif 'filters' in request.cookies:
            filters = request.cookies['filters'].lower().split(',')
    
        if filters == None:
            filters = []
        return filters
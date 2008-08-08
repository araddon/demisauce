import logging

from pylonsdemo.lib.base import *

log = logging.getLogger(__name__)

class HomeController(BaseController):

    def index(self):
        return render('/index.mako')
        
    def cms(self,key):
        # see this route in config/routing.py
        #      map.connect('c/*key', controller='home', action='cms')
        return render('/cms.mako')
    
    def blog(self,key):
        # see this route in config/routing.py
        #  map.connect('c/blog/*key', controller='home', action='blog')
        return render('/cms.mako')
#!/usr/bin/env python
import logging
import urllib
from formencode import Invalid, validators
from formencode.validators import *
import formencode
from sqlalchemy.orm import eagerload

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import meta
from demisauce.model.cms import *
from demisauce.controllers import BaseHandler, RestMixin

log = logging.getLogger(__name__)


class HomeController(RestMixin,BaseHandler):

    def default(self,id=''):
        self.render('index.html')
    
    def gears(self,id=0):
        import datetime
        c.now = datetime.datetime.now()
        self.render('gears.html')
    
    def home(self,id=''):
        self.render('home.html')
    
    def formnew(self):
        self.render('guides/formnew.html')

    def csscolors(self):
        self.render('guides/cssguide.html')
    
    def cssform(self):
        self.render('guides/cssform.html')
    

_controllers = [
    (r"/", HomeController),
    (r"/home/(.*?)", HomeController),
]
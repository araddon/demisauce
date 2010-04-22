#!/usr/bin/env python
import logging
import urllib
from sqlalchemy.orm import eagerload

from demisauce import model
from demisauce.model import meta
from demisauce.model.cms import *
from demisauce.controllers import BaseHandler, RestMixin

log = logging.getLogger('demisauce')


class HomeController(RestMixin,BaseHandler):

    def index(self,id=''):
        self.render("index.html")
    def default(self,id=''):
        self.render('index.html')
    
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
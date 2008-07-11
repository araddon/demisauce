#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
from sqlalchemy.orm import eagerload

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import meta
from demisauce.model.cms import *


log = logging.getLogger(__name__)

def print_hello(*args, **kws):
    alist = []
    alist.append(config['demisauce.url'])
    for arg in args:
        alist.append(arg)
    print 'hello from print hello  %s' % alist
    
class HomeController(BaseController):

    def index(self,key=''):
        return render('/index.html')
    
    def gears(self):
        import datetime
        c.now = datetime.datetime.now()
        return render('/gears.html')
    
    def home(self,key=''):
        return render('/home.html')
    
    def formnew(self):
        return render('/guides/formnew.html')

    def csscolors(self):
        return render('/guides/cssguide.html')
    
    def cssform(self):
        return render('/guides/cssform.html')
    

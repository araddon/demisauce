#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import meta, mapping
from demisauce.model.site import Site
from demisauce.model.email import Email
from demisauce.model.service import Service, App

log = logging.getLogger(__name__)


class ServiceValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    email = formencode.All(validators.Email(resolve_domain=False),
                           validators.String(not_empty=True))

def app_list(site_id):
    pass

class ServiceController(SecureController):
    def __before__(self):
        super(ServiceController, self).__before__()
        c.app_list = [['','']]
        self.site = Site.get(-1,c.site_id)
    
    def index(self):
        c.apps = App.by_site(c.site_id)
        return render('/service/service.html')
    
    def view(self,id=0):
        c.item = App.get(c.user.site_id,id)
        return render('/service/service.html')
    
    def edit(self,id=0):
        log.info('what the heck, in edit %s' % id)
        site = Site.get(-1,c.site_id)
        c.app_list = [['%s' % app.id,app.name] for app in site.apps]
        if id == 0 or id == None:
            c.item = App()
            c.service = Service()
            log.info('hm, id == 0')
        else:
            c.item = App.get(c.user.site_id,id)
            c.service = Service()
        return render('/service/service.html')

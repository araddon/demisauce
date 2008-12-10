#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode

from demisauce.lib.base import *
from demisauce.lib.filter import FilterList, Filter
from demisauce.lib.helpers import dspager
from demisauce import model
from demisauce.model import meta, mapping
from demisauce.model.site import Site
from demisauce.model.email import Email
from demisauce.model.service import Service, App

log = logging.getLogger(__name__)


class ServiceFilter(Filter):
    def __init__(self, name='start', **kwargs):
        Filter.__init__(self,**kwargs)
        self.context = 'service'
        self.name = name
    
    def start(self):
        self.qry = meta.DBSession.query(Service)#.filter_by(site_id=self.site_id)
    
    def filterby_owner(self,filter='mine',offset=0):
        if filter == 'mine':
            self.qry = self.qry.filter(Service.owner_id==c.user.id)
        elif filter == 'all':
            return
    

class ServiceValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    name = formencode.All(String(not_empty=True))

def app_list(site_id):
    pass

class ServiceController(BaseController):
    def __before__(self):
        super(ServiceController, self).__before__()
        c.app_list = [['','']]
        self.site = Site.get(-1,c.site_id)
        
        self.other = []
        if not hasattr(self,'filters'):
            self.filters = FilterList()
            request.environ['filters'] = self.filters
        self.filters.context = 'service'
        if self.filters.current() == None:
            self.filters.set(ServiceFilter(name='owner',clauses={'owner':'all'}))
        if 'filterstatus' in request.params and \
            request.params['filterstatus'] == 'refresh':
            self.filters.set(ServiceFilter(name='owner',clauses={'owner':'all'}))
        c.filters = self.filters
    
    def _filter(self,offset=0,limit=20):
        f = self.filters.current()
        f.start()
        qry = f.finish(offset=offset,limit=limit)
        log.info('offset=%s, limit=%s, f.count=%s' % (offset,limit,f.count))
        
        if offset != 0 and f.count > 0 and f.count >= f.offset:
            c.item = qry[0]
        elif offset == 0 and f.count > 0: #viewlist existing
            c.services = qry
        elif f.count <= f.offset:
            return self.index()
        else:
            c.services = qry
        self.filters.save()
        return self._view()
    
    def _view(self):
        if c.services:
            c.services = dspager(c.services,20)
        
        return render('/service/service.html')
    
    #@requires_role('admin')
    def index(self):
        c.services = Service.all()
        return render('/service/service.html')
    
    def view(self,id=0):
        c.item = Service.get(-1,id)
        return render('/service/service.html')
        
    def owner(self,id=0):
        filter = id
        log.info('other=%s,filter=%s' % (self.other,filter))
        if filter in ['me','mine'] and self.other == []: # new
            self.filters.set(ServiceFilter(name='owner'))
            self.filters.current().clauses['owner'] = 'mine' # filter value
        elif filter == 'all':
            self.filters.set(ServiceFilter(name='owner'))
            self.filters.current().clauses['owner'] = 'all' # filter value
        return self._filter(offset=0,limit=20)
    
    @requires_role('admin')
    def appedit(self,id=0):
        #log.info('what the heck, in edit %s' % id)
        id = request.POST['app_id']
        site = Site.get(-1,c.site_id)
        if id == 0 or id == None or id == '0':
            app = App()
            app.site_id = site.id
            app.owner_id = c.user.id
            log.info('hm, id == 0')
        else:
            app = App.get(site.id,id)
        
        app.name = sanitize(request.POST['app_name'])
        app.description = sanitize(request.POST['description'])
        app.base_url = sanitize(request.POST['base_url'])
        app.save()
        return app.id
    
    @validate(schema=ServiceValidation(), form='edit')
    def service_edit_post(self,id=0):
        
        if self.form_result['service_id'] == "0":
            item = Service(site_id=c.site_id, name=sanitize(self.form_result['name']))
            item.owner_id = c.user.id
        else:
            item = Service.get(c.site_id,self.form_result['service_id'])
        
        item.name = sanitize(self.form_result['name'])
        item.key = sanitize(self.form_result['real_permalink'])
        item.description = sanitize(self.form_result['description'])
        item.format = sanitize(self.form_result['format'])
        item.method_url = sanitize(self.form_result['method_url'])
        if 'list_public' in self.form_result:
            item.list_public = self.form_result['list_public']
        if 'app' in self.form_result:
            item.app_id = self.form_result['app']
        print 'app_id = %s, item.app_id=%s' % (self.form_result['app'],item.app_id)
        if item.id > 0:
            item.save()
        else:
            item.save()
            h.add_alert('Service Added')
        return self.index()
    
    @requires_role('admin')
    @rest.dispatch_on(POST="service_edit_post")
    def edit(self,id=0):
        log.info('what the heck, in service edit %s' % id)
        site = Site.get(-1,c.site_id)
        c.app_list = [['%s' % app.id,app.name] for app in site.apps]
        if id == 0 or id == None:
            c.item = App()
            c.service = Service()
            log.info('hm, id == 0')
        else:
            c.service = Service.get(c.user.site_id,id)
            if not c.service and not c.user.issysadmin:
                h.add_alert('No permission to this service')
                return self.index()
            elif c.user.issysadmin:
                c.service = Service.get(-1,id)
            c.item = c.service.app
        return render('/service/service_edit.html')
    

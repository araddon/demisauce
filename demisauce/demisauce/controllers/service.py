#!/usr/bin/env python
import logging
import urllib
from tornado.options import options
from wtforms import Form, BooleanField, TextField, TextAreaField, \
    PasswordField, SelectField, SelectMultipleField, HiddenField, \
    IntegerField, validators
from wtforms.validators import ValidationError
from demisauce.lib import QueryDict, slugify
from demisauce.lib.sanitize import sanitize
from demisauce.controllers import RestMixin, BaseHandler, requires_admin
from demisauce.lib.helpers import dspager
from demisauce.lib.filter import Filter, FilterList
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
            self.qry = self.qry.filter(Service.owner_id==self.user.id)
        elif filter == 'all':
            return
    

class ServiceForm(Form):
    id              = HiddenField('id',default="0")
    app             = HiddenField('app',default="0")
    name            = TextField('Name', [validators.length(min=4, max=128)])
    description     = TextAreaField('Description')
    slug            = TextField('slug')
    format          = TextField('format')
    base_url        = TextField('Base Url')
    method_url      = TextField('Method Url')
    list_public     = IntegerField('List Public')
    real_permalink  = HiddenField('real_permalink',default="0")

def app_list(site_id):
    pass

class ServiceController(RestMixin,BaseHandler):
    def __before__(self):
        super(ServiceController, self).__before__()
        logging.debug("In __before__")
        app_list = [['','']]
        self.other = []
        if not hasattr(self,'filters'):
            #self.db.cache.delete("filters-personid-%s" % self.current_user.id)
            logging.debug("Creating filter list, passing info")
            self.filters = FilterList(cache=self.db.cache,person_id=self.current_user.id)
        self.filters.context = 'service'
        if self.filters.current() == None:
            self.filters.set(ServiceFilter(name='owner',clauses={'owner':'all'}),
                    cache=self.db.cache)
        if 'filterstatus' in self.request.arguments and \
            self.get_argument("filterstatus") == 'refresh':
            self.filters.set(ServiceFilter(name='owner',clauses={'owner':'all'}))
        self.template_vals.update({'filters':self.filters})
    
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
        self.filters.save(cache=self.db.cache)
        return self._view()
    
    def _view(self):
        if c.services:
            c.services = dspager(c.services,20)
        
        self.render('/service/service.html')
    
    @requires_admin
    def index(self,id=id):
        logging.debug("in index start")
        services = Service.all().filter_by(list_public=1)
        recent = Service.recent_updates(5)
        self.render('service/service.html',services=services,recent=recent)
    
    def view(self,id=0):
        item = Service.get(-1,id)
        self.render('service/service.html',item=item)
    
    def appview(self,id=0):
        item = App.get(-1,id)
        if not (item.list_public or (self.user and self.user.site_id == item.site_id)):
            item = None
        self.render('service/app.html',item=item)
    
    @requires_admin
    def raiseerror(self,id=0):
        raise Exception('for testing')
    
    def owner(self,id=0):
        filter = id
        log.info('other=%s,filter=%s, filters=%s' % (self.other,filter,self.filters))
        if filter in ['me','mine'] and self.other == []: # new
            self.filters.set(ServiceFilter(name='owner'),cache=self.db.cache)
            self.filters.current().clauses['owner'] = 'mine' # filter value
        elif filter == 'all':
            self.filters.set(ServiceFilter(name='owner'),cache=self.db.cache)
            self.filters.current().clauses['owner'] = 'all' # filter value
        return self._filter(offset=0,limit=20)
    
    @requires_admin
    def apps(self,id=0):
        apps = App.by_site(self.user.site_id)
        self.render('/service/app.html',apps=apps)
    
    @requires_admin
    def appeditform(self,id=0):
        if id == 0 or id == None or id == '0':
            item = App()
        else:
            item = App.get(-1,id)
            if not (item.list_public or (self.user and self.user.site_id == item.site_id)):
                item = None
        self.render('/service/app_edit.html',item=item)
    
    @requires_admin
    def appedit(self,id=0):
        #log.info('what the heck, in edit %s' % id)
        id = self.get_argument("app_id")
        site = Site.get(-1,self.user.site_id)
        if id == 0 or id == None or id == '0':
            app = App()
            app.site_id = site.id
            app.owner_id = self.user.id
            log.info('hm, id == 0')
        else:
            app = App.get(site.id,id)
        
        app.slug = sanitize(self.get_argument('real_permalink2'))
        app.name = sanitize(self.get_argument('app_name'))
        app.authn = sanitize(self.get_argument('authn'))
        app.description = sanitize(self.get_argument('description'))
        app.base_url = sanitize(self.get_argument('base_url'))
        app.save()
        return app.id
    
    #@validate(schema=ServiceValidation(), form='edit')
    def edit_POST(self,id=0):
        item = None
        form = ServiceForm(QueryDict(self.request.arguments))
        if form.validate():
            if form.id.data and int(form.id.data) == 0:
                item = Service(site_id=self.user.site_id, name=sanitize(form.name.data))
                item.owner_id = self.user.id
            elif self.user.issysadmin:
                item = Service.get(-1,int(form.id.data))
            else:
                item = Service.get(site_id,int(form.id.data))
        
        item.name = sanitize(form.name.data)
        item.key = sanitize(form.real_permalink.data)
        item.description = sanitize(form.description.data)
        item.format = sanitize(form.format.data)
        item.method_url = sanitize(form.method_url.data)
        if hasattr(form,'list_public'):
            item.list_public = int(form.list_public.data)
        if hasattr(form,'app'):
            item.app_id = form.app.data
        if item.id > 0:
            item.save()
        else:
            item.save()
            self.add_alert('Service Added')
        return self.index()
    
    @requires_admin
    #@rest.dispatch_on(POST="service_edit_post")
    def edit(self,id=0):
        log.info('what the heck, in service edit id=%s' % id)
        site = Site.get(-1,self.user.site_id)
        app_list = [['%s' % app.id,app.name] for app in site.apps]
        if id == 0 or id == None or id=='':
            app = App()
            service = Service()
            log.info('hm, id == 0')
        else:
            service = Service.get(self.user.site_id,id)
            if not service and not self.user.issysadmin:
                h.add_alert('No permission to this service')
                return self.index()
            elif self.user.issysadmin:
                service = Service.get(-1,id)
            if service:
                app = service.app
        self.render('/service/service_edit.html',site=site,app_list=app_list,
            app=app,serviceitem=service)
    

_controllers = [
    (r"/service/(.*?)/(.*?)", ServiceController),
    (r"/service/(.*?)", ServiceController),
]

#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
import simplejson
from sqlalchemy.sql import and_, select, func

from demisauce.lib.base import *
from demisauce.lib.helpers import dspager
from demisauce.lib.filter import FilterList, Filter
from demisauce import model
from demisauce.model import meta, mapping
from demisauce.model.person import Person
from demisauce.model.site import Site
from demisauce.model.email import Email
from demisauce.model.help import Help, HelpResponse, \
    helpstatus, helpstatus_map
from demisauce.model.tag import Tag, TagAssoc

log = logging.getLogger(__name__)

class HelpFilter(Filter):
    def __init__(self, name='status', **kwargs):
        Filter.__init__(self,**kwargs)
        self.context = 'helpadmin'
        self.name = name
    
    def start(self):
        self.qry = meta.DBSession.query(Help).filter_by(site_id=self.site_id)
    
    def filterby_status(self,filter='new',offset=0):
        self.qry = self.qry.filter(Help.status==helpstatus_map[filter])
    def filterby_newness(self,filter='new',offset=0):
        self.qry = self.qry.order_by(Help.created.desc())
    def filterby_tag(self,filter='tag',offset=0):
        self.qry = self.qry.join(['tag_rel','tags'])
        self.qry = self.qry.filter(TagAssoc.type=='help')
        self.qry = self.qry.filter(Tag.value==filter)
    

class HelpProcessFormValidation(formencode.Schema):
    """Form validation for the comment web admin"""
    allow_extra_fields = True
    filter_extra_fields = False
    #title = formencode.All(String(not_empty=True))
    #response = formencode.All(String(not_empty=True))

class HelpadminController(SecureController):
    def __before__(self,**kwargs):
        SecureController.__before__(self)
        self.other = []
        self.filters.context = 'helpadmin'
        if self.filters.current() == None:
            self.filters.set(HelpFilter(name='status',clauses={'status':'new'}))
        if 'filterstatus' in request.params and \
            request.params['filterstatus'] == 'refresh':
            self.filters.set(HelpFilter(name='status',clauses={'status':'new'}))
        c.filters = self.filters
    
    @requires_role('admin')
    def deleted_filters(self,id=0):
        del(session['filters'])
        session.save()
        return 'done'
    
    @requires_role('admin')
    def index(self):
        self.filters.set(HelpFilter())
        return self.viewlist()
    
    def cloud(self,id=0):
        return render('/help/help_cloud.html')
    
    @requires_role('admin')
    def viewlist(self,id=0):
        # viewlist of whatever filter we have
        return self._filter(offset=0,limit=20)
    
    #Marked for removal, was ajax based help method.  
    @requires_role('admin')
    def tag_help(self,id=''):
        data = {'success':False}
        if self.site and 'help_id' in request.params:
            h = Help.get(c.site_id,int(request.params['help_id']))
            h.tags.append(Tag(tag=str(request.params['tag']),person=c.user))
            h.save()
            data = {'success':True,'html':h.id}
        json = simplejson.dumps(data)
        response.headers['Content-Type'] = 'text/json'
        return '%s(%s)' % (request.params['jsoncallback'],json)
    
    def status(self,id=''):
        filter = id
        log.info('other=%s,filter=%s' % (self.other,filter))
        if filter in helpstatus_map and self.other == []: # new
            self.filters.set(HelpFilter(name='status'))
            self.filters.current().clauses['status'] = id # filter value
        elif filter == 'recent' and self.other == []:
            self.filters.set(HelpFilter(name='newness'))
            self.filters.current().clauses['newness'] = id # filter value
        return self._filter(offset=1,limit=1)
    
    def _filter(self,offset=0,limit=20):
        hf = self.filters.current()
        hf.start()
        qry = hf.finish(offset=offset,limit=limit)

        if offset != 0 and hf.count > 0 and hf.count >= hf.offset:
            c.item = qry[0]
        elif offset == 0 and hf.count > 0: #viewlist existing
            c.helptickets = qry
        elif hf.count <= hf.offset and hf.offset > 0:
            return self.index()
        else:
            c.helptickets = qry
        
        self.filters.save()
        return self._view()
    def _view(self):
        if c.item:
            c.item.comments.add_cookies(request.cookies)
        if c.helptickets:
            c.helptickets = dspager(c.helptickets,20)
        
        return render('/help/help_process.html')
    
    def tag(self,id=''):
        #log.debug('other=%s,tag filter=%s' % (self.other,id))
        self.filters.set(HelpFilter(name='tag',clauses={'tag':id}))
        return self._filter(offset=1,limit=1)
    
    @requires_role('admin')
    @rest.dispatch_on(POST="help_process_submit")
    def process(self,id=0):
        c.item = Help.get(c.site_id,id)
        return self._view()
        #return self._filter(offset=1,limit=1,safilter=(Help.id==int(id)))
    
    def next(self,id=0):
        # use existing filter to grab next
        return self._filter(offset=1,limit=1)
        
    def previous(self,id=0):
        # use existing filter to grab previous
        return self._filter(offset=-1,limit=1)
    
    @requires_role('admin')
    @validate(schema=HelpProcessFormValidation(), form='process')
    def help_process_submit(self,id=''):
        h = Help.get(c.user.site_id,int(self.form_result['help_id']))
        if h:
            h.status = int(self.form_result['status'])
            if 'response' in self.form_result and 'publish' in self.form_result:
                item = HelpResponse(help_id=h.id,site_id=c.site_id,
                    person_id=c.user.id)
                if not item.id > 0:
                    h.helpresponses.append(item)
                item.url = h.url
                item.status = h.status
                item.response = sanitize(self.form_result['response'])
                item.title = sanitize(self.form_result['title'])
                item.publish = int(self.form_result['publish'])
            
            if 'tags' in self.form_result:
                h.set_tags(self.form_result['tags'],c.user)
            h.save()
            return self._filter(offset=1,limit=1)
        else:
            #TODO panic?
            log.error('help_process_submit h not found: help_id = %s ' % (self.form_result['help_id']))
        return
    
    @requires_role('admin')
    def view(self,id=0):
        c.item = Help.get(c.user.site_id,id)
        return render('/help/help_process.html')
    

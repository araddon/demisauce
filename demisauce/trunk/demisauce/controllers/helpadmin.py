#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
import simplejson

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import meta, mapping
from demisauce.model.person import Person
from demisauce.model.site import Site
from demisauce.model.email import Email
from demisauce.model.help import Help, HelpResponse, helpstatus
from demisauce.model.tag import Tag

log = logging.getLogger(__name__)

class HelpProcessFormValidation(formencode.Schema):
    """Form validation for the comment web admin"""
    allow_extra_fields = True
    filter_extra_fields = False
    #title = formencode.All(String(not_empty=True))
    #response = formencode.All(String(not_empty=True))

class HelpadminController(SecureController):
    @requires_role('admin')
    def index(self):
        return self.viewlist()
    
    def cloud(self,id=0):
        return render('/help/help_cloud.html')
    
    @requires_role('admin')
    def viewlist(self,id=0):
        c.item = None
        filter = 'new'
        c.all_tags = Tag.by_key(site_id=c.site_id,tag_type='help')
        c.tags_value = 'enter tags separated by commas'
        if 'filter' in request.params:
            filter = request.params['filter']
        
        if filter in helpstatus:
            c.helptickets = Help.by_site(c.user.site_id,20,filter)
        elif filter == 'recent':
            c.helptickets = Help.recent(c.user.site_id,20)
        
        if (id == 0 or id == None) and c.helptickets:
            if c.helptickets.count() > 0:
                c.item = c.helptickets[0]
        elif id > 0:
            c.item = Help.get(c.user.site_id,id)
        if c.item:
            c.tags_value = ','.join(['%s' % tag.value for tag in c.item.tags])
        return render('/help/help_process.html')
    
    @requires_role('admin')
    def tag_help(self,id=''):
        data = {'success':False}
        if self.site and 'help_id' in request.params:
            print 'help_id = %s' % request.params['help_id']
            h = Help.get(c.site_id,int(request.params['help_id']))
            h.tags.append(Tag(tag=str(request.params['tag']),person=c.user))
            h.save()
            data = {'success':True,'html':h.id}
        json = simplejson.dumps(data)
        response.headers['Content-Type'] = 'text/json'
        return '%s(%s)' % (request.params['jsoncallback'],json)
    
    @requires_role('admin')
    @rest.dispatch_on(POST="help_process_submit")
    def process(self,id=0):
        return self.viewlist(id)
    
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
            return self.viewlist()
        else:
            #TODO panic?
            log.error('help_process_submit h not found: help_id = %s ' % (self.form_result['help_id']))
        return
    
    @requires_role('admin')
    def view(self,id=0):
        c.item = Help.get(c.user.site_id,id)
        return render('/help/help_viewone.html')
    

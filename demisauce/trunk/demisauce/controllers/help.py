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
from demisauce.model.person import Person
from demisauce.model.site import Site
from demisauce.model.help import Help


log = logging.getLogger(__name__)

class HelpFormValidation(formencode.Schema):
    """Form validation for the comment web admin"""
    allow_extra_fields = True
    filter_extra_fields = False
    #authorname = formencode.All(String(not_empty=True))
    email = formencode.All(String(not_empty=True))
    content = formencode.All(String(not_empty=True))

class HelpController(BaseController):
    
    def index(self):
        return render('/help/help.html')
    
    @rest.dispatch_on(POST="feedbackform")
    def feedback(self,id):
        site = Site.by_slug(str(id))
        if site:
            c.site_slug = site.slug
        if 'url' in request.params:
            c.current_url = request.params['url']
        else:
            #TODO: fix this 
            c.current_url = 'http://www.google.com'
        return render('/help/help_feedback.html')
    
    @validate(schema=HelpFormValidation(), form='feedback')
    def feedbackform(self,id=''):
        site = Site.by_slug(str(id))
        #print 'feedbackform = %s' % id
        if site:
            c.site = site
            help = Help(site.id,sanitize(self.form_result['email']))
            if c.user:
                help.set_user_info(c.user)
            else:
                if 'authorname' in self.form_result:
                    help.authorname = sanitize(self.form_result['authorname'])
                if 'blog' in self.form_result:
                    help.blog = sanitize(self.form_result['blog'])
                if help.blog == "your blog url":
                    help.blog = ''
            help.url = sanitize(self.form_result['url'])
            help.content = sanitize(self.form_result['content'])
            if 'HTTP_X_FORWARDED_FOR' in request.environ:
                help.ip = request.environ['HTTP_X_FORWARDED_FOR']
            elif 'REMOTE_ADDR' in request.environ:
                help.ip = request.environ['REMOTE_ADDR']
            help.save()
            if 'goto' in request.POST and len(request.POST['goto']) > 5:
                c.goto_url = request.POST['goto']
                print 'should be redirecting %s' % c.goto_url
                return render('/refresh.html')
            else:
                c.result = True
                #print 'should be showing message'
                return render('/help/help_feedback.html')
            
        else:
            #TODO panic?
            pass
        return "whoops, error %s" % id
    


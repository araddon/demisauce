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
from demisauce.model.help import Help
from demisauce.model.cms import Cmsitem
from demisauce.model.rating import Rating

log = logging.getLogger(__name__)


# http://pythonisito.blogspot.com/2008/07/restfulness-in-turbogears.html
class RestMeta(type):
    def __new__(meta,name,bases,dct):
        cls = type.__new__(meta, name, bases, dct)
        allowed_methods = cls.allowed_methods = {}
        for name, value in dct.items():
            #print name, value
            if callable(value) and getattr(value, 'exposed', False):
                allowed_methods[name] = value
        return cls

class ExposedDescriptor(object):
    def __get__(self, obj, cls=None):
        if cls is None: cls = obj
        allowed_methods = cls.allowed_methods
        methodname = request.method.lower()
        if methodname not in allowed_methods:
            raise 'hello'
        return True

class RestMethod(object):
    __metaclass__ = RestMeta
    exposed = ExposedDescriptor()
    def __init__(self, *l, **kw):
        methodname = request.method.lower()
        method = self.allowed_methods[methodname]
        self.result = method(self, *l, **kw)
    
    def __iter__(self):
        return iter(self.result)
    

def make_restful(func):
    """??"""
    def wrapper(*arg):
        print 'in make_restful.wrapper %s' % func
        return func.inner1
    return wrapper

class HelpFormValidation(formencode.Schema):
    """Form validation for the comment web admin"""
    allow_extra_fields = True
    filter_extra_fields = False
    #authorname = formencode.All(String(not_empty=True))
    email = formencode.All(String(not_empty=True))
    content = formencode.All(String(not_empty=True))

class HelpController(BaseController):
    class test(RestMethod):
        #@expose('json')
        def get(self, **kw):
            return dict(method='GET', args=kw)
        #@expose('json')
        def post(self, **kw):
            return dict(method='POST', args=kw)
        #@expose('json')
        def put(self, **kw):
            return dict(method='PUT', args=kw)
        # NOT exposed, for some reason
        def delete(self, **kw):
            return dict(method='DELETE', args=kw)
    
    def index(self):
        data = {'success':True,'help_id':1,'html':render('/help/help.html')}
        json = simplejson.dumps(data)
        #response.headers['Content-Type'] = 'text/json'
        return '[%s]' % (json)
    
    def ratearticle(self,id=''):
        site = Site.by_slug(str(id))
        data = {'success':False}
        if site and 'resource_id' in request.params:
            userid = 0
            #TODO:  add rating_ct to ??? (context?  help?  cms?)
            print 'resource_id = %s' % request.params['resource_id']
            displayname = 'anonymous'
            if c.user:
                userid = c.user.id
                displayname = c.user.displayname
            rating_val = int(request.params['rating'])
            r = Rating(userid,'/ds/help/article',rating_val,sanitize(request.params['resource_id']),displayname)
            r.save()
            data = {'success':True,'html':r.id}
        json = simplejson.dumps(data)
        response.headers['Content-Type'] = 'text/json'
        return '%s(%s)' % (request.params['jsoncallback'],json)
    
    @rest.dispatch_on(POST="feedbackform")
    def feedback(self,id):
        site = Site.by_slug(str(id))
        if site:
            c.site_slug = site.slug
        if 'url' in request.params:
            c.current_url = request.params['url']
        c.isblue = True
        return render('/help/help_feedback.html')
    
    @rest.dispatch_on(POST="feedbackform")
    def submitfeedback(self,id):
        site = Site.by_slug(str(id))
        if site:
            c.site_slug = site.slug
        if 'url' in request.params:
            c.current_url = request.params['url']
        c.hasheader = True
        c.isblue = False
        return render('/help/help_feedback.html')
    
    @validate(schema=HelpFormValidation(), form='feedback')
    def feedbackform(self,id=''):
        site = Site.by_slug(str(id))
        #print 'site = %s' % site
        if site:
            c.site = site
            #print 'setting site.id = %s' % (site.id)
            help = Help(site_id=site.id,email=sanitize(self.form_result['email']))
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
            else:S
                c.result = True
                #print 'should be showing message'
                return render('/help/help_feedback.html')
            
        else:
            #TODO panic?
            pass
        return "whoops, error %s" % id
    


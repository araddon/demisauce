"""The base Controller API

Provides the BaseController class for subclassing, and other objects
utilized by Controllers.
"""
import logging, time, cgi
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, validate, rest
from pylons.i18n import _, ungettext, N_
from pylons.templating import render
from paste.deploy.converters import asbool

from demisauce.lib.filter import FilterList
import demisauce.lib.helpers as h
import demisauce.lib.sanitize as libsanitize
import demisauce.model as model
from demisauce.model import mapping, meta
from demisauce.model.person import Person
import tempita
from functools import wraps
from decorator import decorator

log = logging.getLogger(__name__)

# create scheduler
from demisauce.lib import scheduler
scheduler.start()

def send_emails(email_template,recipient_list,substitution_dict=None):
    """
    Gets an email template from demisauce and sends
    to recipient list using scheduler which runs in the background
    allowing this current request to continue processing
    """
    #print 'in send_emails 1=%s, 2=%s, 3=%s' % (email_template,recipient_list,substitution_dict)
    from demisauce.lib import mail
    from demisaucepy import pylons_helper, demisauce_ws_get
    import urllib
    
    #/api/email/html/your_slug_title_here?apikey=f3f5de7f8376daf29ce3232ca606904ff4adc929
    resource_id = urllib.quote_plus(email_template)
    response = demisauce_ws_get('email',resource_id,format='xml',cache=False)
    if response.success:
        t = response.model
        from string import Template
        s = Template(t.template)
        template = s.substitute(substitution_dict)
        mail.send_mail_toeach((t.subject,
                template, '%s<%s>' % (t.from_name,t.from_email), recipient_list))
        log.debug('sent emails to %s' % recipient_list)
    elif not emails.success:
        log.error('Error retrieving that template')
        return False


base_url = h.base_url

def get_current_user():
    """get current user"""
    user = None
    if 'user' in session and type(session['user']) == Person:
        user = session['user']
    elif 'dsu' in request.cookies:
        user = Person.by_unique(request.cookies['userkey'].lower())
    elif 'userkey' in request.cookies:
        user = Person.by_unique(request.cookies['userkey'].lower())
    return user

def get_current_site():
    """gets site for current request"""
    site = None
    
    if 'apikey' in request.params:
        site = model.site.Site.by_apikey(request.params['apikey'])
    else:
        user = get_current_user()
        if user:
            site = model.site.Site.get(-1,user.site_id)
    return site
    

def requires_role(role):
    def wrapper(func,*args,**kwargs):
        user = get_current_user()
        if not user or user.has_role(role) == False:
            session['return_url'] = request.path_info
            session.save()
            if user:
                if request.environ['pylons.routes_dict']['controller'] == 'dashboard':
                    h.add_alert('Not Authorized')
                    log.info('403, current user doesnt have role=%s redirect to public page' % (role))
                    # TODO:  switch to abort instead of redirect
                    #abort(403, 'Not authorized')
                    redirect_wsave(h.url_for(controller='home',action='index'))
                else:
                    h.add_alert('Not Authorized')
                    log.info('not authorized' )
                    redirect_wsave(h.url_for(controller='dashboard',action='index'))
            else:
                h.add_alert('Must Sign In')
                log.info('not logged in or wrong role, about to redirect to signin' )
                redirect_wsave(h.url_for(controller='account',action='signin'))
        else:
            return func(*args, **kwargs)
    return decorator(wrapper)

def rendertf(filename,vars=[]):
    """Render a Tempita File"""
    fp = open(config['buffet.template_options']['mako.directories'][0]+filename)
    tmpl = tempita.Template(fp.read())
    return tmpl.substitute(vars)

def sanitize(text):
    return libsanitize.Sanitize(text)

def redirect_wsave(*args, **kwargs):
    """
    allows redirect to a destination, but first saves alerts and current
    request messages to something that will still exist on that next
    request
    """
    h.messages_tosession()
    redirect_to(*args, **kwargs)

def print_timing(func):
    """prints how long method took"""
    def wrapper(*arg):
        t2 = time.clock()
        res = func(*arg)
        t3 = time.clock()
        url = request.environ['PATH_INFO']
        method = request.environ['REQUEST_METHOD']
        log.info('%s %s took %0.3fms  %s, %s' % (method,url, (t3-t2)*1000.0,t3,t2))
        return res
    
    return wrapper

# http://pythonisito.blogspot.com/2008/07/restfulness-in-turbogears.html
class RestMethod(object):
    def __call__(self,**kwargs):
        return self.result(**kwargs)
    
    def __init__(self,**kwargs):
        methodname = request.method.lower()
        if hasattr(self,methodname):
            self.result = getattr(self, methodname)
    

class BaseController(WSGIController):
    requires_auth = False
    
    def redirect(self,url):
        """docstring for redirect"""
        redirect_wsave(url)
    
    def start_session(self,user,remember_me=False):
        if user:
            session['user'] = user
            site = user.site
            c.user = user
            session.save()
            if remember_me == True:
                expire_seconds = 60*60*24*31
                response.set_cookie('userkey', user.user_uniqueid,path='/',
                        expires=expire_seconds)
                response.set_cookie('email', user.email,path='/',
                        expires=expire_seconds, secure=True)
                response.set_cookie('test', user.email,path='/',
                            expires=expire_seconds)
            log.debug('in base controller setting user ')
    
    def __before__(self):
        """
            request.cookies['userkey']
            session['current_user_person'] = user
        """
        c.form_errors = c.form_errors or {}
        self.user = get_current_user()
        self.site = get_current_site()
        c.user = self.user
        c.site = self.site
        c.debug = False
        if 'debug' in config:
            c.debug = config['debug']
        if c.user:
            c.site_id = c.user.site_id
            self.filters = FilterList(site_id=c.site_id)
            request.environ['filters'] = self.filters
        c.base_url = h.base_url()
        c.help_url = h.help_url()
        c.adminsite_slug = config['demisauce.appname']
        c.demisauce_url = config['demisauce.url']
    
    @print_timing
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method the
        # request is routed to. This routing information is available in
        # environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            #log.debug('in base controller __call__ remove session' )
            if meta.DBSession:
                meta.DBSession.remove()
    

class SecureController(BaseController):
    requires_auth = True
    
    @requires_role('admin')
    def __before__(self):
        BaseController.__before__(self)
    

class NeedsadminController(BaseController):
    requires_auth = True
    
    @requires_role('sysadmin')
    def __before__(self):
        BaseController.__before__(self)
    


# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']

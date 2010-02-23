import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.escape
from tornado.options import options
import os, logging, functools, urllib
import re, datetime, random, string
from demisauce import model
from demisauce.lib import helpers, sanitize as libsanitize
from demisauce.model.user import Person
from demisauce.lib import assetmgr
import demisauce
import webhelpers
import json
import httplib, urllib2, urllib, time, string
import base64

from functools import wraps
from decorator import decorator

log = logging.getLogger(__name__)

def requires_authn(method):
    """Decorate methods with this to require that the user be logged in"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user or not self.current_user.is_authenticated:
            if self.request.method == "GET":
                url = self.get_login_url()
                if "?" not in url:
                    url += "?" + urllib.urlencode(dict(next=self.request.uri))
                self.redirect(url)
                return
            raise tornado.web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper
    

def requires_admin(method):
    """Decorate methods with this to require that the user be logged in
        and that they be an admin"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user or not self.current_user.is_authenticated:
            if self.request.method == "GET":
                url = self.get_login_url()
                if "?" not in url:
                    url += "?" + urllib.urlencode(dict(next=self.request.uri))
                logging.debug("not current_uesr, redirect to url %s" % url)
                self.redirect(url)
                return
            raise tornado.web.HTTPError(403)
        elif not self.current_user.issysadmin and not self.current_user.isadmin:
            if self.request.method == "GET":
                self.redirect('/?msg=Not+Authorized')
                return
            raise tornado.web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper

def requires_sysadmin(method):
    """Decorate methods with this to require that the user be logged in
        and that they be an admin"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user or not self.current_user.is_authenticated:
            if self.request.method == "GET":
                url = self.get_login_url()
                if "?" not in url:
                    url += "?" + urllib.urlencode(dict(next=self.request.uri))
                logging.debug("not current_uesr, redirect to url %s" % url)
                self.redirect(url)
                return
            raise tornado.web.HTTPError(403)
        elif not self.current_user.issysadmin:
            if self.request.method == "GET":
                self.redirect('/?msg=Not+Authorized')
                return
            raise tornado.web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper

def send_emails(email_template,recipient_list,substitution_dict=None):
    """
    Gets an email template from demisauce and sends
    to recipient list using scheduler which runs in the background
    allowing this current request to continue processing
    """
    from demisaucepy import mail
    from demisaucepy import demisauce_ws_get
    import urllib
    
    resource_id = urllib.quote_plus(email_template)
    response = demisauce_ws_get('email',resource_id,format='xml',cache=False)
    if response.success:
        t = response.model
        from string import Template
        if hasattr(t,'template'):
            s = Template(t.template)
            template = s.substitute(substitution_dict)
            mail.send_mail_toeach((t.subject,
                template, '%s<%s>' % (t.from_name,t.from_email), recipient_list))
            log.debug('sent emails to %s' % recipient_list)
        else:
            log.error('Error retrieving that template 1')
    elif not emails.success:
        log.error('Error retrieving that template 2')
        return False


def requires_role(role):
    def wrapper(func,*args,**kwargs):
        user = self.get_current_user()
        if not user or user.has_role(role) == False:
            session['return_url'] = request.path_info
            session.save()
            if user:
                if request.environ['pylons.routes_dict']['controller'] == 'dashboard':
                    self.add_alert('Not Authorized')
                    log.info('403, current user doesnt have role=%s redirect to public page' % (role))
                    # TODO:  switch to abort instead of redirect
                    #abort(403, 'Not authorized')
                    redirect_wsave(h.url_for(controller='home',action='index'))
                else:
                    self.add_alert('Not Authorized')
                    log.info('not authorized' )
                    redirect_wsave(h.url_for(controller='dashboard',action='index'))
            else:
                self.add_alert('Must Sign In')
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
    return libsanitize.sanitize(text)

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

class RestMethod(object):
    def __call__(self,**kwargs):
        return self.result(**kwargs)
    
    def __init__(self,**kwargs):
        methodname = request.method.lower()
        if hasattr(self,methodname):
            self.result = getattr(self, methodname)
    

class HelloHandler(tornado.web.RequestHandler):
    def __init__(self,application,request, transforms=None):
        super(HelloHandler,self).__init__(application,request,transforms=transforms)
    
    def get(self):
        self.write("hello world!")
    

class BaseHandler(tornado.web.RequestHandler):
    #@print_timing
    def __init__(self, application, request, transforms=None):
        tornado.web.RequestHandler.__init__(self, application, request, transforms=transforms)
        logging.debug("%s path %s class=%s__init__" % (self.request.method.upper(), 
            self.request.path,self.__class__))
        #logging.debug('headers = %s' % self.request.headers)
        self.session = {}
        self._messages = []
        self.msg_errors = []
        self.msg_alerts = []
        self.form_errors = []
        next = ""
        #logging.debug("user-agent:  %s" % self.request.headers['User-Agent'])
        #logging.debug("RemoteIP = %s" % request.remote_ip )
        if self.get_argument("next",None) is not None:
            logging.debug(urllib.urlencode({"next":self.get_argument("next","")}))
            next = urllib.urlencode({"next":self.get_argument("next","")})
        
        self.site = self.get_current_site()
        
        self.template_vals = {'current_userisadmin':False,
                    "next":next,
                    "debug":self.application.settings['debug'],
                    "xsrf_token":self.xsrf_token,
                    "base_url":self.application.settings['base_url'],
                    "settings":self.application.settings,
                    "requestargs":self.request.arguments,
                    "h":webhelpers.html.tags,
                    "h2":demisauce.lib.helpers,
                    "site":self.site,
                    "base_url":helpers.options.base_url,
                    "url":self.request.path}
        
        self.jinja2_env = self.settings.get("jinja2_env") 
        self.user = self.get_current_user()
        self.__before__()
    
    @property
    def db(self):
        return self.application.db
    
    requires_auth = False
    def get_current_user(self):
        """get current user"""
        if not hasattr(self,"_current_user") or self.get_argument("reload",None):
            #logging.debug("get_current_user:  no _current_user attr, finding")
            user_cookie = self.get_secure_cookie("dsuser")
            if not user_cookie: return None
            self._user_json = tornado.escape.json_decode(user_cookie)
            if 'id' not in self._user_json:
                return None
            
            if self.get_argument("reload",None):
                redis_user_json = None
            else:
                logging.debug("get_current_user: found cookie, getting user from redis")
                redis_user_json = self.db.redis.get("DS-person-%s" % self._user_json['id'])
            
            if not redis_user_json:
                p = None
                if self.get_cookie("dsu",None):
                    p = Person.by_unique(self.get_cookie("dsu").lower())
                elif self.get_cookie("dsuserkey",None):
                    p = Person.by_unique(self.get_cookie("dsuserkey").lower())
                if p:
                    self.set_current_user(p,islogon=False)
                    redis_user_json = p.to_json()
            
            # make sure current_user returned is NOT an SA Person obj, but pure json derived
            if redis_user_json:
                p = Person()
                self._current_user = p.from_json(redis_user_json)
            else:
                self._current_user = None
                logging.error("Critical error get_current_user() no redis_user_json user_json=%s" % self._user_json)
        
        #logging.debug(self._user_json)
        if not self._current_user: return None
        
        # set is authenticated/not flag, make sure not to persist this other than cookie
        if 'is_authenticated' in self._user_json:
            self._current_user.is_authenticated = self._user_json['is_authenticated']
        else:
            self._current_user.is_authenticated = False
        return self._current_user
    
    def get_current_site(self):
        """gets site for current request"""
        site = None
        if hasattr(self,"site"):
            return self.site
        if 'apikey' in self.request.arguments:
            site = model.site.Site.by_apikey(self.get_argument('apikey'))
            #log.debug("found site by apikey=%s, site=%s" % (self.get_argument('apikey'),site))
        else:
            user = self.get_current_user()
            if user and user.is_authenticated:
                site = model.site.Site.get(-1,user.site_id)
        return site
    
    def __before__(self):
        pass
    
    def set_current_user(self,sauser,remember_me = False,is_authenticated = False, islogon=True):
        """Set the current user into current request and persistence"""
        logging.debug("set_current_user ")
        if islogon:
            sauser.last_login = datetime.datetime.now()
            sauser.save()
        user_dict = sauser.to_dict_basic()
        
        user_cookie = self.get_secure_cookie("dsuser")
        if user_cookie: 
            _user_json = tornado.escape.json_decode(user_cookie)
            if "is_authenticated" in _user_json and _user_json['is_authenticated'] == True \
                and _user_json['id'] == user_dict['id']:
                # if user is being updated due to profile updates, it won't have
                # is_authenticated, but since they are already authenticated then 
                # respect it
                is_authenticated = True
            elif _user_json['id'] != user_dict['id']:
                self.clear_cookie('dsuser')
        
        # don't add this is_authenticated to redis!!! Or memcached, use cookie
        user_dict.update({"is_authenticated":is_authenticated})
        logging.debug("set_current_user:  user_hash = %s" % user_dict)
        self.set_secure_cookie("dsuser", tornado.escape.json_encode(user_dict)) #,domain=options.demisauce_domain
        self.set_secure_cookie("dsuser", tornado.escape.json_encode(user_dict),domain='blog.demisauce.com')
        self.set_cookie("dsuserkey",sauser.user_uniqueid)
        user_json = sauser.to_json()
        #logging.error("set_current_user: about to put into redis:  %s" % user_json)
        self._current_user = Person().from_json(user_json)
        self.user = self._current_user
        self._user_json = user_dict
        self.db.redis.set("DS-person-%s" % sauser.id,user_json)
    
    def redirect_wsave(self, *args, **kwargs):
        """
        allows redirect to a destination, but first saves alerts and current
        request messages to something that will still exist on that next
        request
        """
        self.messages_tosession()
        self.redirect_to(*args, **kwargs)
    
    def redirect(self,url,msg=None,qs=None):
        """Redirect, send msg, additional qs parameters, look for next"""
        next = self.get_argument("return_url",None)
        if next:
            url = next
        if msg and url.find('?') > 0:
            url = "%s&msg=%s" % (url,urllib.quote_plus(msg))
        elif msg:
            url = "%s?msg=%s" % (url,urllib.quote_plus(msg))
        
        if qs and url.find('?') > 0:
            url = "%s&%s" % (url,qs)
        elif qs:
            url = "%s?%s" % (url,qs)
        super(BaseHandler, self).redirect(url)
    
    def add_msg(self,msg,msgtype='human'):
        self._messages.append((msg,msgtype))
    
    def finish(self, chunk=None):
        self.db.finish()
        tornado.web.RequestHandler.finish(self,chunk)
    
    def get_error_html(self, status_code):
        """Custom UI error handler"""
        logging.error("in get_error_html %s, method=%s" % (status_code,self.request.method))
        logging.error("In get error template vals = %s" % self.template_vals)
        return self.render_string("error.html",code=status_code,
            message=httplib.responses[status_code],**self.template_vals)
    
    def render(self,template_file, **kwargs):
        """
        Helper method to render the appropriate template
        """
        self.template_vals.update({'messages':self._messages,
            'msg_box':self.msg_box(),
            'error_box':self.error_box()})
        self.template_vals.update(kwargs)
        super(BaseHandler,self).render(template_file,**self.template_vals)
    
    def render_string(self, template_name, **kwargs): 
        # if the jinja2_env is present, then use jinja2 to render templates: 
        if self.jinja2_env: 
            if self.settings.get("debug") or not getattr(tornado.web.RequestHandler, "_templates", None): 
                tornado.web.RequestHandler._templates = {} 
            template_path = self.settings.get("template_path") 
            if template_path not in tornado.web.RequestHandler._templates: 
                tornado.web.RequestHandler._templates[template_path] = self.jinja2_env 
        return tornado.web.RequestHandler.render_string( self, template_name, **kwargs ) 
    
    def add_alert(self,msg):
        """
        Use this from controllers to add a system message
        """
        if not hasattr(self,'msg_alerts'):
            self.msg_alerts = []
        self.msg_alerts.append(msg)
    
    def messages_tosession(self):
        """
        moves all local messages to session for a redirect
        """
        raise NotImplemented("no session in tornado")
        msgs = []#[c.form_errors[k]  for k in c.form_errors.keys()]
        msgs += [x  for x in self.msg_errors]
        self.session['errors'] = msgs
        msgs = [x  for x in self.msg_alerts]
        self.session['messages'] = msgs
        self.session.save()
    
    def add_error(self,msg):
        """
        Use this from controllers to add an error message
        """
        if not hasattr(self,'msg_errors'):
            self.msg_errors = []
        self.msg_errors.append(msg)
    
    def error_box(self):
        if 'errors' in self.session:
            self.msg_errors = self.msg_errors or []
            self.msg_errors += session['errors'] 
        
        s = ''
        if (self.form_errors and len(self.form_errors) > 0) or \
            (self.msg_errors and len(self.msg_errors) > 0):
            s += '<img src="/static/images/error.png" class="ib"/>'
        if (self.form_errors and len(self.form_errors) > 0):
            s += 'There were errors on the form highlighted below'
        s += ''.join(["%s <br />" % (x)  for x in self.msg_errors])
        return (len(s) > 0 or '') and ("$.ds.humanMsg.displayMsg('%s');" % s)
        return (len(s) > 0 or '') and helpers.round_box(s)
    
    def msg_box(self):
        if 'messages' in self.session:
            self.msg_alerts = self.msg_alerts or []
            self.msg_alerts += self.session['messages'] 
            del(session['messages'])
            #session.save()
        
        s = '' + ''.join(["%s <br />" % (x)  for x in self.msg_alerts])
        return (len(s) > 0 or '') and ("$.ds.humanMsg.displayMsg('%s');" % s)
        return (len(s) > 0 or '') and helpers.round_box(s)
    

class RestMixin(object):
    def _do_method(self,method="GET",action='default',id=0,**kwargs):
        if method == "POST" and hasattr(self,"%s_POST" % action):
            getattr(self,"%s_POST" % action)(id=id,**kwargs)
        elif hasattr(self,action):
            getattr(self,action)(id=id,**kwargs)
        elif hasattr(self,'index'):
            getattr(self,'index')(id=id,**kwargs)
        else:
            raise Exception("why is it getting here?")
            raise tornado.web.HTTPError(404)
    
    def get(self,action='default',id=0, **kwargs):
        logging.debug("RestMixin.get  action %s" % (action))
        self._do_method(method="GET",action=action,id=id,**kwargs)
    
    def post(self,action='default',id=0,**kwargs):
        logging.debug("POST action = %s" % action)
        self._do_method(method="POST",action=action,id=id,**kwargs)
    

class SecureController(BaseHandler):
    requires_auth = True
    
    @requires_admin
    def __before__(self):
        BaseHandler.__before__(self)
    

class CrossDomain(BaseHandler):
    def get(self):
        self.render("crossdomain.xml")
    

class UploadHandler(BaseHandler):
    def get(self):
        self.write('hello')
    
    def post(self):
        if 'photo' in self.request.arguments:
            filewpath = assets.stash_file(self.get_argument('photo'))
            logging.debug("Uploaded from mobile app: %s" % filewpath)
            self.write("{filename:'%s', status: 'success'}" % (filewpath))
        else:
            f = self.request.files['userfile'][0]
            logging.debug("upladed file:  %s  type=%s" % (f['filename'],f['content_type']))
            #TODO:  Check that it is image type first eh
            filewpath = assetmgr.stash_file(base64.encodestring(f['body']),f['filename'],
                    gearman_client=self.db.gearman_client)
            #self.write("{filename:'%s', status: 'success'}" % (filewpath))
            self.write(filewpath)
    

class NeedsadminController(BaseHandler):
    requires_auth = True
    
    @requires_sysadmin
    def __before__(self):
        BaseHandler.__before__(self)

class CustomErrorHandler(BaseHandler):
    def __init__(self,application,request,error_code):
        self.error_code = error_code
        super(CustomErrorHandler,self).__init__(application,request)
    
    def get(self):
        self.set_status(self.error_code)
        logging.error("ErrorHandler:  code=%s, path=%s" % (self.error_code,self.request.path) )
        self.render("error.html",code=self.error_code,
            message=httplib.responses[self.error_code])
    

_controllers = [
    (r"/hello", HelloHandler),
    (r"/upload(?:\/)?", UploadHandler),
    (r"/crossdomain\.xml", CrossDomain),
] 




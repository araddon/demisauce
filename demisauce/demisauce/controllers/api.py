#!/usr/bin/env python
import logging
import urllib
import json
import tornado.escape
from tornado.options import options
from sqlalchemy.sql import and_
from demisauce.controllers import BaseHandler, requires_authn
from demisauce import model
from demisauce.model import meta
from demisauce.model.site import Site
from demisauce.model.email import Email
from demisauce.model.person import Person
from demisauce.model.activity import Activity
from demisauce.model.service import Service
from gearman import GearmanClient
from gearman.task import Task

log = logging.getLogger(__name__)

def requires_api(method):
    """Decorate methods with this to require that the user be logged in
        and that they be an admin"""
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
        elif not self.current_user.is_sysadmin:
            if self.request.method == "GET":
                self.redirect('/?msg=Not+Authorized')
                return
            raise tornado.web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper


class RestMethod(object):
    def __init__(self,db,site,action='all',id='all',start=0,limit=100,request=None):
        self.db = db
        self.site=site
        self.object = None
        self.start=start
        self.limit=limit
        self.id = id
        self.action=action
        self.qry = []
        self.request = request
    
    def json(self):
        json_data = [self.json_formatter(row) for row in self.qry]
        return json.dumps(json_data)
    
    def json_formatter(self,o):
        """default json formatter, uses JsonMixin """
        if o:
            return o.to_dict()
        return ''
    
    def handle_post(self,postargs,get_func):
        if not self.object:
            return []
        
        for key in self.__class__.object_cls._json_api_keys:
            if key in postargs:
                if get_func(key) == 'true':
                    setattr(self.object,key,True)
                elif get_func(key) == 'false':
                    setattr(self.object,key,False)
                else:
                    setattr(self.object,key,get_func(key)) 
                logging.debug("setting key,val = %s, %s" % (key,get_func(key)))
        self.object.save()
    
    def get_object(self,id):
        self.id = id
        self.object = self.__class__.object_cls.get(id)
        self.qry = [self.object]
    
    def list(self,q=None):
        if not q:
            logging.debug("In list.q limit = %s" % self.limit)
            qry = self.db.session.query(self.__class__.object_cls).limit(self.limit)
            if self.start > 0:
                logging.debug("self.start = %s" % self.start)
                qry = qry.offset(self.start)
        else:
            qry = self.db.session.query(self.__class__.object_cls).filter(
                    self.__class__.object_cls.name.like('%' + q + '%'))
        self.qry = qry
    
    def do_delete(self):
        if self.object and hasattr(self.object,'delete'):
            self.object.delete()
    

class RestMethodJsonPost(RestMethod):
    def handle_post(self,postargs,get_func):
        if not self.request:
            return


def requires_site(target):
    """
    A decorator to protect the API methods to be able to
    accept api by either apikey or logged on user, in future oath?
    """
    def decorator(self,*args,**kwargs):
        site = self.get_current_site() 
        if not self.site:
            log.info('403, api call ' )
            return self.nonresponse(403)
        else:
            return target(self,*args,**kwargs)
    return decorator

def requires_site_slug(target):
    """allows access with only a slug which identifies a site
    but isn't really secure  """
    def decorator(self,*args):
        site = get_current_site() 
        if not site:
            log.info('403, api call ' )
            return self.nokey()
        else:
            return target(self,*args)
    return decorator
    

class ApipublicController(object):
    def activity(self,id=''):
        if not self.user and 'hashedemail' in request.params: 
            user = person.Person.by_hashedemail(str(request.params['hashedemail']))
        elif self.user:
            user = self.user
        else:
            return ''
        if 'site_slug' in request.params:
            site_slug = str(request.params['site_slug'])
        if 'activity' in request.params:
            action = str(request.params['activity'])
        a = activity.Activity(site_id=user.site_id,person_id=user.id,activity=action)
        if 'ref_url' in request.params:
            a.ref_url = request.params['ref_url']
        if 'category' in request.params:
            a.category = request.params['category']
        if 'cnames' in request.params:
            names = [n for n in request.params['cnames'].split(',') if n != '']
            if len(names) > 0:
                a.custom1name = names[0]
                a.custom1val = request.params[names[0]]
            if len(names) > 1:
                a.custom2name = names[1]
                a.custom2val = request.params[names[1]]
        a.save()
        return a.id
    

class ApiControllerOld(object):
    def __before__(self):
        BaseController.__before__(self)
        
        # Authentication required?
        if self.site and self.site.id > 0:
            request.environ['api.isauthenticated'] = 'true'
            request.environ['site'] = self.site
        else:
            log.debug('no apikey or self.user')
    
    def nokey(self):
        """
        returns error code for no api key
        """
        response.headers['Content-Type'] = 'application/xhtml+xml'
        return "<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n" + \
                "<exception id=\"401\" >Invalid API Key</exception>" 
    
    def connect(self,format='html',id=''):
        """
        Used by clients to test connectivity
        returns
            'connected, valid api key' if api key is valid
            'invalid api key but connected' if api key isn't valid
        """
        if self.site and self.site.id > 0:
            return 'connected, valid api key'
        else:
            return 'invalid api key but connected'
    
    @requires_site
    def cms(self,format='html',id=''):
        if not 'site' in request.environ:
            return self.nokey()
        
        c.len = 0
        from demisauce.model.cms import Cmsitem
        if id != '' and id != None:
            rid = urllib.unquote_plus(id)
            c.cmsitems = meta.DBSession.query(Cmsitem).filter_by(rid=rid).all()
            if (c.cmsitems and len(c.cmsitems) == 1) and \
                (c.cmsitems[0].item_type == "folder" or \
                c.cmsitems[0].item_type == 'root'):
                c.cmsitems = [itemassoc.item for itemassoc in c.cmsitems[0].children]
        else:
            c.cmsitems = meta.DBSession.query(Cmsitem).all()
        
        c.resource_id = id
        if c.cmsitems == []:
            log.debug('404, no items rid=%s' % id)
            abort(404, 'No items found')
        
        if format == 'html':
            self.render('/api/cms.html')
        elif format == 'xml':
            response.headers['Content-Type'] = 'application/xhtml+xml'
            c.len = len(c.cmsitems)
            self.render('/api/cms.xml')
        elif format == 'script':
            self.render('/api/cmsjs.js')
        else:
            raise 'not implemented'
    
    @requires_site
    def help(self,format='script',id=''):
        if id != '' and id != None:
            rid = urllib.unquote_plus(id)
            c.cmsitems = meta.DBSession.query(cms.Cmsitem).filter_by(rid=rid).all()
            if (c.cmsitems and len(c.cmsitems) == 1) and \
                (c.cmsitems[0].item_type == "folder" or \
                c.cmsitems[0].item_type == 'root'):
                c.cmsitems = [itemassoc.item for itemassoc in c.cmsitems[0].children]
            
        if c.site and c.site.id:
            url = id.replace('root/help','')
            topinfo = help.HelpResponse.for_url(c.site,url,5)
            c.topinfo = [hr for hr in topinfo] # get something that can do a len()
            log.debug('url=%s, topinfo = %s' % (url,c.topinfo))
        
        c.resource_id = id
        results = render('/api/cms.html')
        data = {'success':True,'html':results,'key':id}
        jsonstring = json.dumps(data)
        if format == 'json':
            response.headers['Content-Type'] = 'text/json'
            return '%s(%s)' % (request.params['jsoncallback'],jsonstring)
        else:
            return results
        #self.render('/api/cmsjs.js')
    
    @requires_site
    def comment(self,format='json',id=''):
        site = request.environ['site']
        #site2 = Site.by_slug(str(id))
        #if site2.id != site.id and 'apikey' in request.params and request.params['apikey'] == site2.key:
        #    site = site2 # logged in user not same as 
        c.len = 0
        
        if id != '' and id != None:
            rid = urllib.unquote_plus(id)
            log.info('comment rid= %s' % id)
            c.comments = Comment.for_url(site_id=site.id,url=rid)
        else:
            c.comments = Comment.all(site.id)
        
        c.items = c.comments
        c.resource_id = urllib.quote_plus(id)
        
        if format == 'html':
            self.render('/api/comment.html')
        elif format == 'xml':
            response.headers['Content-Type'] = 'application/xhtml+xml'
            if c.comments == []:
                #log.info('404, no comments siteid=%s, uri=%s' %(site.id,rid))
                #abort(404, 'No items found')
                c.len = 0 # no comments is ok, right?
            else:
                c.len = len(c.comments)
            self.render('/api/comment.xml')
        elif format == 'view':
            c.show_form = True
            c.source = 'remote_html'
            c.len = len(c.comments)
            c.hasheader = True
            c.site_slug = site.slug
            #raise 'eh'
            self.render('/comment/comment_nobody.html')
        elif format == 'json':
            self.render('/api/comment.js')
        else:
            raise NotImplementedError('format of type %s not supported' % format)
    
    @requires_site
    def email(self,format='html',id='',**kw):
        site = request.environ['site']
        class email(RestApiMethod):
            def get(self, **kw):
                self.render('/api/email.xml')
            def post(self, **kw):
                return 'not implemented'
            def put(self, **kw):
                return 'not implemented'
            def delete(self, **kw):
                return 'not implemented'
        
        if id != '' and id != None:
            c.emailtemplates = Email.by_key(site_id=site.id,key=id)  
            if c.emailtemplates:
                c.item = c.emailtemplates
                c.emailtemplates = [c.item]       
        else:
            c.emailtemplates = Email.all(site_id=site.id)
        
        if not c.emailtemplates:
            log.info('no email templates?  Should be site=%s' % site)
            c.emailtemplates = []
        
        kw.update({'format':format})
        return email()(**kw)
    
    @requires_site
    def send_email(self,format='xml',id=''):
        """
        Sends an email, accepts dictionary of info
        that it will hash into email to send
        """
        if not 'site' in request.environ:
            return self.nokey()
        
        if id != '' and id != None:
            site = request.environ['site']
            email = Email.by_key(site.id,id)
            if email:
                c.item = email
            
    
    #@requires_site
    def service(self,format='xml',id='',**kw):
        #site = request.environ['site']
        class servicerest(RestApiMethod):
            def get(self, **kw):
                self.render('/api/service.xml')
            def post(self, **kw):
                return 'not implemented'
            def put(self, **kw):
                return 'not implemented'
            def delete(self, **kw):
                return 'not implemented'
        
        if id != '' and id != None:
            app,service = id.split('/')
            services = model.service.Service.by_app_service(appkey=app,servicekey=service)  
            if services:
                c.services = [services]       
        else:
            c.services = model.service.Service.all()
        
        if not c.services:
            log.info('no services?  Should be id=%s' % id)
        
        kw.update({'format':format})
        return servicerest()(**kw)
    
    @requires_site
    def person(self,format='xml',id=''):
        if c.site:
            verb = request.environ['REQUEST_METHOD'].lower()
            p = None
            if verb == 'get':
                if id == '' or id == None:
                    c.persons = person.Person.by_site(c.site.id)
                else:
                    p = person.Person.by_hashedemail(c.site.id,id)
                    c.persons = [p]
            elif verb == 'post' or verb == 'put':
                postvals = {}
                p = person.Person.by_hashedemail(c.site.id,id)
                for pkey in request.params:
                    postvals[pkey] = request.params[pkey]
                if p == None: # new not edit
                    p = person.Person(site_id=c.site.id,email=request.params['email'])
                if 'authn' in request.params:
                    p.authn = request.params['authn']
                if 'displayname' in request.params:
                    p.displayname = request.params['displayname']
                p.save()
                c.persons = [p]
            elif verb == 'delete':
                return 'delete'
            else:
                return 'what?'
            response.headers['Content-Type'] = 'application/xhtml+xml'
            
            self.render('/api/person.xml')
        else:
            log.info('person: no site key %s' % (c.site))
            return 'no site key'
    
    @requires_site
    def group(self,format='xml',id=0, **kwargs):
        if c.site:
            verb = request.environ['REQUEST_METHOD'].lower()
            g = group.Group.get(c.site.id,id)
            if not g or not g.site_id == c.site.id:
                #g = None
                return 'crap %s' % id
            if verb == 'get':
                pass
            elif verb == 'post' or verb == 'put':
                postvals = {}
                for pkey in request.params:
                    postvals[pkey] = request.params[pkey]
                else:
                    g = group.Group(c.site.id,request.params['name'])
                if 'authn' in request.params:
                    g.authn = request.params['authn']
                if 'displayname' in request.params:
                    g.displayname = request.params['displayname']
                g.save()
            elif verb == 'delete':
                return 'delete'
            else:
                return 'what?'
            response.headers['Content-Type'] = 'application/xhtml+xml'
            c.groups = [g]
            self.render('/api/group.xml')
        else:
            return 'no site key'
    
    @requires_site
    def poll(self,format='xml',id='',**kw):
        site = request.environ['site']
        if site:
            p = None
            c.polls = []
            if id != '' and id != None:
                id = str(urllib.unquote_plus(id))
            
            if id == '' or id == None:
                c.polls = poll.Poll.by_site(site.id)
            else:
                p = poll.Poll.by_key(site.id,id)
                if p is None:
                    c.polls = []
                elif type(p) != list:
                    c.polls = [p]
            class pollrest(RestApiMethod):
                def get(self, **kw):
                    self.render('/api/poll.xml')
                def post(self, **kw):
                    raise NotImplementedError('not implemented')
                def put(self, **kw):
                    raise NotImplementedError('not implemented')
                def delete(self, **kw):
                    raise NotImplementedError('not implemented')
            
            if format == 'xml':
                response.headers['Content-Type'] = 'application/xhtml+xml'
            elif p is not None and format == 'view':
                return '%s %s' % (p.html,p.results)
            kw.update({'format':format})
            return pollrest()(**kw)
        else:
            return 'no site key'
    

class ApiHandler(BaseHandler):
    def nonresponse(self,status_code):
        self.set_status(status_code)
        self.write("{'status':'failure'}")
        return
    
    def do_api_method(self,http_method="get",noun=None,id='list', action=None,format="json"):
        object_id = 0
        # /api/noun/id/action.format?apikey=key&limit=100&start=101
        # /api/noun/id/selector(action).format
        # /api/noun.format shortcut for /api/noun/list.format or /api/noun/all.format
        # /api/noun/id.format
        format = format if format is not None else "json"
        id = 'list' if (id == '' or id == 'all') else id
        format = format.replace('.','')
        q = self.get_argument("q",None)
        limit = self.get_argument("limit",'100')
        if not limit.isdigit():
            limit = 100
        else:
            limit = int(limit)
            limit = 1000 if limit > 1000 else limit
        start = self.get_argument("start",'0')
        if not start.isdigit():
            start = 0
        else:
            start = int(start)
        logging.debug("API: noun=%s, id=%s, action=%s, format=%s, url=%s, start=%s, limit=%s" % (noun,id,action,format,self.request.path,start,limit))
        
        if noun in {}:
            api_handler = {}[noun](self.db,self.site,action=action,id=id,
                    limit=limit,start=start,request=self.request)
            jsonstring = '{}'
            if id and id == 'list':
                api_handler.list(q=q)
                logging.debug("found list request")
            else:
                id = int(id) if id.isdigit() else id
                logging.debug("get_object %s" % id)
                api_handler.get_object(id)
            
            if http_method == 'post':
                logging.debug("BODY = %s" % (self.request.body))
                logging.debug("POST ARGS: %s" % (self.request.arguments))
                api_handler.handle_post(self.request.arguments,self.get_argument)
            elif http_method == 'delete':
                api_handler.delete()
            
            #  ===== Which data to show, prep formatting
            if action in ['addupdate','delete']:
                jsonstring = '{"msg":"success"}'
            elif action == 'list' or action == 'get':
                logging.debug("list/get json()")
                jsonstring = api_handler.json()
            elif hasattr(api_handler,action):
                logging.debug("custom action = %s" % action)
                jsonstring = getattr(api_handler,action)()
            else: 
                jsonstring = api_handler.json()
            
            # ==== Serialization Format
            if format == 'json':
                self.set_header("Content-Type", "application/json")
                if 'jsoncallback' in self.request.arguments:
                    self.write('%s(%s)' % (self.get_argument('jsoncallback'),jsonstring))
                elif 'callback' in self.request.arguments:
                    self.write('%s(%s)' % (self.get_argument('callback'),jsonstring))
                else:
                    self.write('%s' % (jsonstring))
            elif format == 'xml':
                self.set_header("Content-Type", 'application/xhtml+xml')
                
        
        else:
            raise tornado.web.HTTPError(404)
    
    def get(self,noun=None,id='all',action=None,format="json"):
        log.debug("in api handler")
        self.do_api_method("get",noun, id,action,format)
    
    def post(self,noun=None,id='all',action=None,format="json"):
        self.do_api_method("post",noun, id,action,format)
    
    def delete(self,noun=None,id='all',action=None,format="json"):
        logging.info("in DELETE")
        self.do_api_method("delete",noun, id,action,format)
    

class ApiSimpleHandler(ApiHandler):
    @requires_site
    def get(self,noun=None,id=0,format="json"):
        logging.debug("hit on simple handler")
        super(ApiSimpleHandler,self).get(noun,id,'get',format)
    
    @requires_site
    def post(self,noun=None,id=0,format="json"):
        logging.debug("in simple handler")
        super(ApiSimpleHandler,self).post(noun,id,'addupdate',format)
    
    @requires_site
    def delete(self,noun=None,id=0,format="json"):
        logging.debug("in simple handler")
        super(ApiSimpleHandler,self).delete(noun,id,'delete',format)
    


class ApiBaseHandler(BaseHandler):
    def normalize_args(self,noun=None,requestid=None,action=None,format="json"):
        "Normalizes and formats arguments"
        self.format = format if format is not None else "json"
        self.format = self.format.replace('.','')
        self.noun = noun
        self.qry = []
        self.object = None
        if requestid is None or requestid in ['',None,'all']:
            # /api/noun.format 
            # /api/noun/list.format
            # /api/noun/all.format
            self.id = 'list'
            action = 'list'
        else:
            # /api/noun/id/action.format?apikey=key&limit=100&start=101
            # /api/noun/id/selector(action).format
            # /api/noun/id.format
            # /api/noun/siteslug?more
            if requestid and hasattr(requestid,'isdigit') and \
                (type(requestid) == int or requestid.isdigit()):
                self.id = int(requestid)
            else:
                self.id = requestid
            
            if action == None:
                action = 'get'
        
        self.action = action
        
        # find query, start, limi
        self.q = self.get_argument("q",None)
        self.limit = self.get_argument("limit",'100')
        if not self.limit.isdigit():
            self.limit = 100
        else:
            self.limit = int(self.limit)
            self.limit = 1000 if self.limit > 1000 else self.limit
        self.start = self.get_argument("start",'0')
        if not self.start.isdigit():
            self.start = 0
        else:
            self.start = int(self.start)
    
    def json(self):
        json_data = [self.json_formatter(row) for row in self.qry]
        return json.dumps(json_data)
    
    def json_formatter(self,o):
        """default json formatter, uses JsonMixin """
        if o:
            return o.to_dict()
        return ''
    
    def handle_post(self,postargs,get_func):
        if not hasattr(self,'object') or not self.object:
            return []
        
        for key in self.__class__.object_cls._json_api_keys:
            if key in postargs:
                if get_func(key) == 'true':
                    setattr(self.object,key,True)
                elif get_func(key) == 'false':
                    setattr(self.object,key,False)
                else:
                    setattr(self.object,key,get_func(key)) 
                logging.debug("setting key,val = %s, %s" % (key,get_func(key)))
        self.object.save()
    
    def action_get_object(self,id):
        self.object = self.__class__.object_cls.get(id)
        self.qry = [self.object]
    
    def action_get_list(self,q=None):
        if not q:
            logging.debug("In list.q limit = %s" % self.limit)
            qry = self.db.session.query(self.__class__.object_cls).limit(self.limit)
            if self.start > 0:
                logging.debug("self.start = %s" % self.start)
                qry = qry.offset(self.start)
        else:
            qry = self.db.session.query(self.__class__.object_cls).filter(
                    self.__class__.object_cls.name.like('%' + q + '%'))
        self.qry = qry
    
    def do_delete(self):
        if self.object and hasattr(self.object,'delete'):
            self.object.delete()
    
    def nonresponse(self,status_code):
        self.set_status(status_code)
        self.write("{'status':'failure'}")
        return
    
    def do_action(self):
        jsonstring = '{}'
        
        if self.id and self.id == 'list':
            self.action_get_list(q=self.q)
            logging.debug("found list request")
        elif self.id and self.action == 'get':
            logging.debug("do_action, id=%s,action=%s" % (self.id,self.action))
            self.action_get_object(self.id)
        elif self.request.method == "POST" and hasattr(self,"%s_POST" % self.action):
            getattr(self,"%s_POST" % self.action)()
        elif hasattr(self,self.action):
            logging.debug("custom action = %s" % self.action)
            getattr(self,self.action)()
        else:
            logging.debug("get_object %s" % self.id)
            self.action_get_object(self.id)
    
    def render_json(self,jsonstring):
        self.set_header("Content-Type", "application/json")
        if 'jsoncallback' in self.request.arguments:
            self.write('%s(%s)' % (self.get_argument('jsoncallback'),jsonstring))
        elif 'callback' in self.request.arguments:
            self.write('%s(%s)' % (self.get_argument('callback'),jsonstring))
        else:
            self.write('%s' % (jsonstring))
    
    def render_to_format(self):
        #  ===== Which data to show, prep formatting
        if self.format == 'json':
            if self.action in ['addupdate','delete']:
                jsonstring = '{"msg":"success"}'
            elif self.action == 'list' or self.action == 'get':
                logging.debug("list/get json()")
                jsonstring = self.json()
            elif hasattr(self,self.action):
                logging.debug("rendering self.json() for custom action = %s" % self.action)
                jsonstring = self.json()
            else: 
                jsonstring = self.json()
        
        # ==== Serialization Format
        if self.format == 'json':
            self.render_json(jsonstring)
        elif self.format == 'xml':
            self.set_header("Content-Type", 'application/xhtml+xml')
    
    def get(self,noun=None,requestid='all',action=None,format="json"):
        self.normalize_args(noun, requestid,action,format)
        logging.debug("API: noun=%s, id=%s, action=%s, format=%s, url=%s, start=%s, limit=%s" % (self.noun,self.id,self.action,self.format,self.request.path,self.start,self.limit))
        self.do_action()
        self.render_to_format()
    
    def post(self,noun=None,requestid='all',action=None,format="json"):
        self.normalize_args(noun, requestid,action,format)
        logging.debug("API: noun=%s, id=%s, action=%s, format=%s, url=%s, start=%s, limit=%s" % (self.noun,self.id,self.action,self.format,self.request.path,self.start,self.limit))
        self.do_action()
        self.handle_post(self.request.arguments,self.get_argument)
        self.render_to_format()
    
    def delete(self,noun=None,requestid='all',action=None,format="json"):
        logging.info("in DELETE")
        self.normalize_args(noun, requestid,action,format)
        self.do_action()
        self.do_delete()
        self.render_to_format()
    

class ApiSecureHandler(ApiBaseHandler):
    @requires_site
    def get(self,noun=None,requestid='all', action=None,format="json"):
        super(ApiSecureHandler,self).get(noun,requestid,action,format)
    
    @requires_site
    def post(self,noun=None,requestid="all", action=None,format="json"):
        super(ApiSecureHandler,self).post(noun,requestid,action,format)
    

class ActivityApiHandler(ApiBaseHandler):
    object_cls = Activity
    def action_get_object(self,id):
        self.object = None
        self.qry = []
    
    def get(self,site_slug='',format="json"):
        #logging.debug("hit on activity handler")
        #super(ActivityApiHandler,self).get(noun="activity",id=site_slug,action='get',format=format)
        if not self.user and 'hashedemail' in self.request.arguments: 
            user = person.Person.by_hashedemail(str(self.get_argument('hashedemail')))
        elif self.user:
            user = self.user
        else:
            return 
        
        if 'site_slug' in self.request.arguments:
            site_slug = str(self.get_argument('site_slug'))
        if 'activity' in self.request.arguments:
            activity_name = str(self.get_argument('activity'))
        
        a = Activity(site_id=user.site_id,person_id=user.id,activity=activity_name)
        if 'ref_url' in self.request.arguments:
            a.ref_url = self.get_argument('ref_url')
        if 'category' in self.request.arguments:
            a.category = self.get_argument('category')
        if 'cnames' in self.request.arguments:
            names = [n for n in self.get_argument('cnames').split(',') if n != '']
            if len(names) > 0:
                a.custom1name = names[0]
                a.custom1val = request.params[names[0]]
            if len(names) > 1:
                a.custom2name = names[1]
                a.custom2val = request.params[names[1]]
        a.save()
    
    @requires_site
    def post(self,site_slug='',format="json"):
        requestid = site_slug
        super(ActivityApiHandler,self).post('activity',requestid,'addupdate',format=format)
    
    def options(self,site_slug='',format='json'):
        logging.debug("in activity api OPTIONS")
    

class EmailApiHandler(ApiSecureHandler):
    object_cls = Email
    def action_get_object(self,id):
        if type(id) == int:
            self.object = Email.get(site_id=self.site.id,id=id) 
        else:
            self.object = Email.by_key(site_id=self.site.id,key=id)  
        if self.object:
            self.qry = [self.object]
        else:
            logging.error("no email %s" % self.id)
    
    def send(self):
        logging.error("in send of email api")
        emailjson = json.loads(self.request.body)
        if emailjson and 'template_name' in emailjson:
            logging.error("weehah, body json = %s" % emailjson)
            #TODO:  revamp and use self.db.gearman_client
            gearman_client = GearmanClient(options.gearman_servers)
            gearman_client.do_task(Task("email_send",self.request.body, background=True))
    
    def json_formatter(self,o):
        if o:
            keys=['key','name','subject','from_email',
                'reply_to','id','from_name','template','to']
            output = o.to_dict(keys=keys)
            return output
        return None
    
    def action_get_list(self,q=None):
        if q:
            qry = self.db.session.query(Email).filter(and_(
                Email.name.like('%' + qry + '%'),Email.site_id==self.site.id))
        else:
            qry = Email.all(site_id=self.site.id)
            logging.debug("in email list, qry = %s" % qry)
        self.qry = qry
    

class PersonAnonApi(ApiBaseHandler):
    object_cls = Person
    def init_user(self):
        # Need site?   
        user_key = self.id
        site_slug = self.db.cache.get(str(user_key))
        if site_slug:
            site = Site.by_slug(site_slug)
            if site:
                user = meta.DBSession.query(Person).filter_by(
                    site_id=site.id, hashedemail=user_key).first()
                if not user:
                    p = Person(hashedemail=user_key)
                    p.save()
            self.set_current_user(user,is_authenticated = True)
            self.write("{'status':'success'}")
            logging.info("tried to init_user succeeded")
        else:
            logging.error("tried to init_user failed site_slug =%s, user_key = %s" % (site_slug,user_key))
            self.write("{'status':'failure'}")
    

class PersonApiHandler(ApiSecureHandler):
    object_cls = Person
    def json_formatter(self,o):
        if o:
            output = o.to_dict(keys=['name','displayname','id','email','url',
                'hashedemail','user_uniqueid','foreign_id'])
            #if o.region and o.region.id > 0:
            #    output['region'] = o.region.to_dict(keys=['name','metro_code']) # keys=['name','metro_code']
            return output
        return None
    
    def action_get_list(self,q=None):
        if q:
            qry = self.db.session.query(Person).filter(and_(
                Person.name.like('%' + qry + '%'),Person.is_anonymous==1))
        else:
            qry = self.db.session.query(Person).filter(and_(Person.site_id==self.site.id))
        self.qry = qry
    
    def pre_init_user(self):
        """A push to pre-initiate session (step 1) optional
        body of json to add/update user"""
        user_key = self.id
        self.db.cache.set(str(user_key),self.site.slug)
        user = None
        if self.request.method == 'POST' and self.request.body:
            user_dict = json.loads(self.request.body)
            logging.debug("Loaded data user_dict=%s" % user_dict)
            user = meta.DBSession.query(Person).filter_by(
                site_id=self.site.id, email=user_dict['email'].lower()).first()
            if not user:
                p = Person(email=user_dict['email'].lower(),
                        displayname=user_dict['displayname'],
                        site_id=self.site.id)
                p.save()
                user = p
            else:
                pass
                #TODO:  update user
        else:
             user = meta.DBSession.query(Person).filter_by(
                    site_id=self.site.id, hashedemail=user_key).first()
        if user:
            self.object = user
            self.qry = [user]
    
    def options(self,site_slug='',format='json'):
        logging.debug("in person api OPTIONS")
    

class ServiceApiHandler(ApiSecureHandler):
    object_cls = Service
    def action_get_object(self,id):
        self.object = Service.by_app_service(servicekey=id)  
        if self.object:
            self.qry = [self.object]
        else:
            logging.error("no service %s" % self.action)
    
    def json_formatter(self,o):
        if o:
            keys=['key','name','format','url',
                'views','id','method_url','cache_time','description']
            output = o.to_dict(keys=keys)
            if o.site and o.site.id > 0:
                output['site'] = o.site.to_dict(keys=['name','base_url']) 
            if o.app and o.app.id > 0:
                output['app'] = o.app.to_dict(keys=['name','description','authn','base_url']) 
            return output
        return None
    
    def action_get_list(self,q=None):
        if q:
            qry = self.db.session.query(Service).filter(and_(
                Service.name.like('%' + qry + '%'),Service.list_public==True))
        else:
            qry = self.db.session.query(Service).filter(Service.list_public==True)
            logging.debug("in services list, qry = %s" % qry)
        self.qry = qry
    


""" GET  : get
    POST : add/update
    DELETE: delete
    
    /api/noun/id/(action|filter|property)
    (?:\/)?
    
    (r"/api/(.*?)/([0-9]*?|.*?|all|list)/(.*?)(?:\.)?(json|xml|custom)?", ApiSecureHandler),
    (r"/api/(.*?)/([0-9]*?|.*?|all|list)(.json|.xml|.custom)?", ApiSimpleHandler),
"""
_controllers = [
    (r"/api/(activity)/(.*?)", ActivityApiHandler),
    (r"/api/(user|person)/(.*?)/(init_user|tbdmorestuff)", PersonAnonApi),
    (r"/api/(user|person)/([0-9]*?|.*?)/(.*?)(?:\.)?(json|xml|custom)?", PersonApiHandler),
    (r"/api/(user|person)/(.*?)(.json|.xml|.custom)", PersonApiHandler),
    (r"/api/(user|person)/(.*?)", PersonApiHandler),
    (r"/api/(email)/([0-9]*?|.*?|all|list)/(.*?)(?:\.)?(json|xml|custom)?", EmailApiHandler),
    (r"/api/(email)/(.*?)(.json|.xml|.custom)", EmailApiHandler),
    (r"/api/(service)/([0-9]*?|.*?|all|list)/(.*?)(?:\.)?(json|xml|custom)?", ServiceApiHandler),
    (r"/api/(service)/(.*?)(.json|.xml|.custom)", ServiceApiHandler),
]

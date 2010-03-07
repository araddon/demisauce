import logging, urllib, json, hashlib
import tornado.escape
from tornado.options import options
from sqlalchemy.sql import and_
from sqlalchemy.orm import eagerload
from demisauce.controllers import BaseHandler, requires_authn
from demisauce import model
from demisauce.model import meta
from demisauce.model.site import Site
from demisauce.model.email import Email
from demisauce.model.user import Person, Group
from demisauce.model.activity import Activity
from demisauce.model.service import Service, App
from demisauce.model.object import Object
from gearman import GearmanClient
from gearman.task import Task
from demisaucepy import cache, cache_setup

log = logging.getLogger(__name__)
CACHE_DURATION = 600 if not options.debug else 1


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

class ApiBaseHandler(BaseHandler):
    def __init__(self, application, request, transforms=None):
        super(ApiBaseHandler, self).__init__(application, request, transforms=transforms)
        self.set_status(200)
    
    def nokey(self):
        """
        returns error code for no api key
        """
        response.headers['Content-Type'] = 'application/xhtml+xml'
        return "<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n" + \
                "<exception id=\"401\" >Invalid API Key</exception>"
    
    def args_todict(self):
        d = {}
        for k in self.request.arguments.keys():
            d[k] = self.get_argument(k)
        return d
    
    def is_json_post(self):
        'Determines if json post?'
        if self.request.body:
            if self.request.body.find("{") > -1 and self.request.body.find("{") < 4 or \
                self.request.body.find("[") > -1 and self.request.body.find("[") < 4:
                return True
        return False
    
    def normalize_args(self,noun=None,requestid=None,action=None,format="json"):
        "Normalizes and formats arguments"
        self.format = format if format is not None else "json"
        self.format = self.format.replace('.','')
        self.noun = noun
        self.qry = []
        self.object = None
        self._result = None
        #log.debug("in normalize:  noun=%s, requestid=%s, action=%s" % (noun,requestid,action))
        if requestid is None or requestid in ['',None,'all','list']:
            # /api/noun.format 
            # /api/noun/list.format
            # /api/noun/all.format
            # /api/noun/all/selector(action).format
            # /api/noun/list/selector(action).format
            self.id = 'list'
            #action = 'list'
            if action == None:
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
        if self.qry and self.qry != []:
            json_data = []
            for row in self.qry:
                data = self.json_formatter(row) 
                if isinstance(data,(list)):
                    json_data = json_data + data
                else:
                    # normally it is a dict
                    json_data.append(data)
            return json.dumps(json_data)
        else:
            return None
    
    def json_formatter(self,o):
        """default json formatter, uses JsonMixin """
        if o:
            return o.to_dict()
        return ''
    
    def object_load_dict(self,o,data_dict):
        'http post handle args'
        return data_dict
    
    def _add_object(self,data_dict):
        o = None
        if self.id not in ['',None,'list','get','all']:
            self.action_get_object(self.id, data_dict)
            o = self.object
            if not o:
                o = self.__class__.object_cls()
                o.site_id = self.site.id
                if len(self.qry) == 0:
                    self.qry.append(o)
            log.debug("about to update %s" % data_dict)
            data_dict = self.object_load_dict(o,data_dict)
            o.from_dict(data_dict,allowed_keys=self.__class__.object_cls._allowed_api_keys)
            o.after_load()
        
        if o and o.isvalid():
            self.object = o
            log.debug("saving updated object")
            o.save()
            cache.cache.delete(cache.cache_key(self.request.full_url()))
            self.set_status(201)
        else:
            log.error("what went wrong, not valid %s" % o)
    
    def handle_post(self):
        logging.debug("in handle post, args= %s, body=%s" % (self.request.arguments,self.request.body))
        if self.is_json_post():
            log.debug("yes, json post")
            pyvals = json.loads(self.request.body)
            if pyvals and isinstance(pyvals,dict):
                self._add_object(pyvals)
            elif pyvals and isinstance(pyvals,list):
                for json_data in pyvals:
                    self._add_object(json_data)
        else:
            self._add_object(self.args_todict())
    
    def action_get_object(self,id, data_dict = {}):
        if self.id > 0:
            self.object = self.__class__.object_cls.saget(id)
        if self.object:
            self.qry = [self.object]
        else:
            self.qry = []
    
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
        if self.id and self.id not in ['list','all']:
            self.action_get_object(self.id)
        if self.object and hasattr(self.object,'delete'):
            url = self.request.full_url()
            logging.info("DELETE id=%s for url=%s" % (self.id,url))
            self.object.delete()
            self.object = None
            self.qry = None
            self.set_status(204)
            cache.cache.delete(cache.cache_key(url))
        else:
            logging.error("not found?   %s, %s" % (self.noun, self.id))
    
    def nonresponse(self,status_code):
        self.set_status(status_code)
        self.write("{'status':'failure'}")
        return
    
    def do_get(self):
        if self._has_cache():
            return
        if self.id and self.id == 'list' and self.action == 'list':
            self.action_get_list(q=self.q)
            logging.debug("found list request")
        elif self.id and self.action == 'get':
            logging.debug("do_get, id=%s,action=%s" % (self.id,self.action))
            self.action_get_object(self.id)
        elif hasattr(self,self.action):
            logging.debug("custom action = %s" % self.action)
            getattr(self,self.action)()
        else:
            logging.debug("get_object %s" % self.id)
            self.action_get_object(self.id)
        if self.object is None and self.qry == [] and self._status_code == 200:
            self.set_status(404)
    
    def do_post(self):
        if hasattr(self,"%s_POST" % self.action):
            getattr(self,"%s_POST" % self.action)()
        elif self.action not in ['list','get','post','all','json','delete'] and \
                hasattr(self,self.action):
            logging.debug("POST %s" % self.action)
            getattr(self,self.action)()
        else:
            self.handle_post()
    
    def render_json(self,jsonstring):
        self.set_header("Content-Type", "application/json")
        if 'jsoncallback' in self.request.arguments:
            self.write('%s(%s)' % (self.get_argument('jsoncallback'),jsonstring))
        elif 'callback' in self.request.arguments:
            self.write('%s(%s)' % (self.get_argument('callback'),jsonstring))
        else:
            self.write('%s' % (jsonstring))
    
    def _has_cache(self):
        if not 'cache' in self.request.arguments:
            url = self.request.full_url()
            result = cache.cache.get(cache.cache_key(url))
            if result:
                log.debug("found cache")
                self._result = result
                return True
        return False
    
    def do_cache(self,result_string,duration=CACHE_DURATION):
        url = self.request.full_url()
        cache.cache.set(cache.cache_key(url),result_string,duration)
    
    def render_to_format(self):
        _stringout = None
        #  ===== Which data to show, prep formatting
        if self.format == 'json' and not self._result:
            if self.action in ['addupdate','delete']:
                _stringout = '{"msg":"success"}'
            elif self.action == 'list' or self.action == 'get':
                _stringout = self.json()
            elif hasattr(self,self.action):
                _stringout = self.json()
            else: 
                _stringout = self.json()
        # objectid
        if self.request.method in ('POST','PUT','DELETE') and self.object:
            self.set_header("X-Demisauce-ID", str(self.object.id))
        
        # ==== Serialization Format
        if self.format == 'json':
            if _stringout:
                self.render_json(_stringout)
                if self.request.method == 'GET':
                    self.do_cache(_stringout)
            elif self._result:
                self.render_json(self._result)
        elif self.format == 'xml':
            self.set_header("Content-Type", 'application/xhtml+xml')
    
    def get(self,noun=None,requestid='all',action=None,format="json"):
        self.normalize_args(noun, requestid,action,format)
        logging.debug("API: noun=%s, id=%s, action=%s, format=%s, url=%s, start=%s, limit=%s" % (self.noun,self.id,self.action,self.format,self.request.path,self.start,self.limit))
        self.do_get()
        logging.debug("in get status = %s" % (self._status_code))
        self.render_to_format()
    
    def post(self,noun=None,requestid='all',action=None,format="json"):
        self.normalize_args(noun, requestid,action,format)
        logging.debug("POST API: noun=%s, id=%s, action=%s, format=%s, url=%s, start=%s, limit=%s" % (self.noun,self.id,self.action,self.format,self.request.path,self.start,self.limit))
        self.do_post()
        self.render_to_format()
    
    def put(self,noun=None,requestid='all',action=None,format="json"):
        self.normalize_args(noun, requestid,action,format)
        logging.debug("PUT API: noun=%s, id=%s, action=%s, format=%s, url=%s, start=%s, limit=%s" % (self.noun,self.id,self.action,self.format,self.request.path,self.start,self.limit))
        self.do_post()
        self.render_to_format()
    
    def delete(self,noun=None,requestid='all',action=None,format="json"):
        logging.info("in DELETE")
        self.normalize_args(noun, requestid,action,format)
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
    def action_get_object(self,id, data_dict = {}):
        self.object = None
        self.qry = []
    
    def get(self,site_slug='',format="json"):
        if not self.user and 'hashedemail' in self.request.arguments: 
            user = user.Person.by_hashedemail(str(self.get_argument('hashedemail')))
        elif self.user:
            user = self.user
        else:
            return
        
        if 'site_slug' in self.request.arguments:
            site_slug = str(self.get_argument('site_slug'))
        if 'activity' in self.request.arguments:
            activity_name = str(self.get_argument('activity'))
        
        a = Activity(site_id=user.site_id,person_id=user.id,activity=activity_name)
        a.ip = self.request.remote_ip 
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
    def action_get_object(self,id, data_dict = {}):
        if type(id) == int and id > 0:
            self.object = Email.get(site_id=self.site.id,id=id) 
        elif id == 0 and data_dict.has_key('slug'):
            logging.debug("they asked for id = 0, lets ignore and doublecheck slug = %s" % data_dict['slug'])
            self.object = Email.by_slug(site_id=self.site.id,slug=data_dict['slug'])  
            if self.object:
                logging.debug("found object, sweet!  %s" % self.object.id)
        else:
            logging.debug("trying to get by slug %s" % (id))
            self.object = Email.by_slug(site_id=self.site.id,slug=id)  
        if self.object:
            self.qry = [self.object]
        else:
            self.set_status(404)
            logging.error("no email %s, status=%s" % (self.id, self._status_code))
    
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
            keys=['slug','name','subject','from_email',
                'reply_to','id','from_name','template','to']
            output = o.to_dict(keys=keys)
            return output
        return None
    
    def action_get_list(self,q=None):
        if q:
            qry = self.db.session.query(Email).filter(and_(
                Email.name.like('%' + q + '%'),Email.site_id==self.site.id))
        else:
            qry = Email.all(site_id=self.site.id)
            logging.debug("in email list, qry = %s" % qry)
        self.qry = qry
    

class PersonAnonApi(ApiBaseHandler):
    object_cls = Person
    def init_user(self):
        # Need site?   
        ds_id = self.id
        site_key = self.db.cache.get(str(ds_id))
        logging.debug("init_user ds_id,site_key = %s = %s" % (ds_id,site_key))
        if site_key:
            site = Site.by_apikey(str(site_key))
            if site:
                user = Person.get(site.id,ds_id)
                if not user:
                    logging.error("user not found? id = %s" % ds_id)
            else:
                logging.error("no site? %s" % ds_id)
                
            self.set_current_user(user,is_authenticated = True)
            logging.debug("tried to init_user succeeded")
            self.set_status(204) # succuess, no content
        else:
            logging.error("tried to init_user failed ds_id = %s" % (ds_id))
            self.set_status(400)
            self.write("{'status':'failure'}")
    

class PersonApiHandler(ApiSecureHandler):
    object_cls = Person
    def change_email(self):
        self.handle_post()
    
    def delete_by_get(self):
        self.action_get_object(self.id)
        if self.object and hasattr(self.object,'delete'):
            self.object.delete()
            self.object = None
            self.qry = None
            self.set_status(204)
        else:
            logging.error("not found?   %s, %s" % (self.noun, self.id))
    
    def action_get_object(self,id, data_dict = {}):
        if isinstance(self.id,int) and self.id > 0:
            self.object = Person.get(self.site.id,self.id)
            if not self.object:
                self.object = Person.by_foreignid(self.site.id,self.id)
        elif isinstance(self.id,int) and self.id == 0 and 'email' in data_dict:
            self.object = Person.by_email(self.site.id,data_dict['email'].lower())
        elif 'foreign_id' in data_dict:
            self.object = Person.by_foreignid(self.site.id,data_dict['foreign_id'])
        else:
            self.object = Person.by_hashedemail(self.site.id,self.id)
            log.debug('getting by hashed:  %s, %s' % (self.id, self.object))
        if self.object:
            self.qry = [self.object]
    
    def json_formatter(self,o):
        if o:
            logging.debug("in person api handler  %s" % o.profile_url)
            output = o.to_dict(keys=['name','displayname','id','email','profile_url','url',
                'hashedemail','foreign_id','authn','extra_json'])
            #if o.region and o.region.id > 0:
            #    output['region'] = o.region.to_dict(keys=['name','metro_code']) # keys=['name','metro_code']
            return output
        return None
    
    def action_get_list(self,q=None):
        if q:
            qry = self.db.session.query(Person).filter(and_(
                Person.name.like('%' + q + '%'),Person.is_anonymous==1))
        else:
            qry = self.db.session.query(Person).filter(and_(Person.site_id==self.site.id))
        self.qry = qry
    
    def pre_init_user(self):
        """A push to pre-initiate session (step 1) optional
        body of json to add/update user"""
        user = None
        user_dict = {}
        if self.request.method == 'POST':
            if self.is_json_post():
                user_dict = json.loads(self.request.body)
            else:
                user_dict = self.args_todict()
            logging.debug("Loaded data user_dict=%s" % user_dict)
            self.action_get_object(self.id, user_dict)
            if not self.object:
                logging.debug("creating new user, not found %s dict=%s" % (self.id,user_dict))
                self.object = Person(site_id=self.site.id,foreign_id=self.id)
            if self.object:
                self.object.from_dict(user_dict,allowed_keys=Person._allowed_api_keys)
                self.object.save()
            
        else:
            self.action_get_object(self.id)
        
        if self.object:
            user_key = self.object.id
            logging.debug("setting cache = %s, %s" % (str(user_key),self.site.key))
            self.db.cache.set(str(user_key),self.site.key,120) # 2 minutes only
            site_key = self.db.cache.get(str(user_key))
            logging.debug("site_key, self.site.key = %s, %s" % (site_key, self.site.key))
            assert site_key == self.site.key
            
            self.qry = [self.object]
    
    def options(self,site_slug='',format='json'):
        logging.debug("in person api OPTIONS")
    

class ServiceApiHandler(ApiSecureHandler):
    object_cls = Service
    def action_get_object(self,id, data_dict = {}):
        if isinstance(id,int) and self.id > 0:
            self.object = Service.saget(id)  
        elif isinstance(id,int) and self.id == 0:
            if 'key' in data_dict:
                self.object = Service.by_app_service(data_dict['key'])  
        else:
            self.object = Service.by_app_service(self.id)  
        if self.object:
            self.qry = [self.object]
        else:
            self.set_status(404)
            logging.error("no service %s for %s" % (self.id,self.request.full_url()))
    
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
                Service.name.like('%' + q + '%'),Service.list_public==True))
        else:
            qry = self.db.session.query(Service).filter(Service.list_public==True)
            logging.debug("in services list, qry = %s" % qry)
        self.qry = qry
    

class AppApiHandler(ApiSecureHandler):
    object_cls = App
    def action_get_object(self,id, data_dict = {}):
        if isinstance(id,int) and self.id > 0:
            self.object = App.saget(id)  
        elif isinstance(id,int) and self.id == 0:
            if 'slug' in data_dict:
                self.object = App.by_slug(self.site.id,slug=data_dict['slug'])
        else:
            self.object = App.by_slug(site_id=self.site.id,slug=self.id)  
        
        if self.object:
            self.qry = [self.object]
        else:
            self.set_status(404)
            logging.error("no service %s" % self.id)
    
    def json_formatter(self,o):
        if o:
            keys=['slug','name','owner_id','site_id',
                'list_public','id','base_url','url_format','authn','description']
            output = o.to_dict(keys=keys)
            output['services'] = []
            for svc in o.services:
                output['services'].append(svc.to_dict(keys=['key','name','format','url',
                    'views','id','method_url','cache_time','description']) )
            return output
        return None
    
    def action_get_list(self,q=None):
        if q:
            qry = self.db.session.query(Service).filter(and_(
                App.name.like('%' + q + '%'),App.list_public==True))
        else:
            qry = self.db.session.query(App).filter(App.list_public==True)
            logging.debug("in services list, qry = %s" % qry)
        self.qry = qry
    

class SiteApiHandler(ApiSecureHandler):
    object_cls = Site
    def _add_object(self,data_dict):
        if self.site.is_sysadmin == True or self.site.id == self.id:
            super(SiteApiHandler, self)._add_object(data_dict=data_dict)
        else:
            self.set_status(403)
    
    def action_get_object(self,id, data_dict = {}):
        if self.site.is_sysadmin == True or self.site.id == self.id:
            if type(id) == int and id > 0:
                self.object = Site.saget(id) 
            elif type(id) == int and id == 0 and 'slug' in data_dict:
                logging.debug("they asked for id = 0, lets ignore and doublecheck slug = %s" % data_dict['slug'])
                self.object = Site.by_slug(data_dict['slug'])
            else:
                logging.debug("they asked for id = %s, lets ignore and doublecheck slug" % (self.id))
                self.object = Site.by_slug(self.id)   
            if self.object:
                self.qry = [self.object]
            else:
                self.set_status(404)
                logging.error("no site %s, status=%s" % (self.id, self._status_code))
        
    
    def json_formatter(self,o):
        if o:
            keys=['email','name','slug','description','id','extra_json',
                'base_url','site_url','created','enabled','public']
            output = o.to_dict(keys=keys)
            if o.apps:
                output['apps'] = []
                for app in o.apps:
                    appd = {}
                    appd = app.to_dict(keys=['name','description','authn','base_url']) 
                    appd['services'] = []
                    for svc in app.services:
                        appd['services'].append(svc.to_dict(keys=['key','name','format','url',
                            'views','id','method_url','cache_time','description']) )
                    output['apps'].append(appd)
            return output
        return None
    
    def action_get_list(self,q=None):
        if q:
            qry = self.db.session.query(Service).filter(and_(
                Service.name.like('%' + q + '%'),Service.list_public==True))
        else:
            qry = self.db.session.query(Service).filter(Service.list_public==True)
            logging.debug("in services list, qry = %s" % qry)
        self.qry = qry
    

class ObjectApiHandler(ApiSecureHandler):
    object_cls = Object
    def delete_by_get(self):
        self.action_get_object(self.id)
        if self.object and hasattr(self.object,'delete'):
            self.object.delete()
            self.object = None
            self.qry = None
            self.set_status(204)
        else:
            logging.error("not found?   %s, %s" % (self.noun, self.id))
    
    def object_load_dict(self,o,data_dict):
        'http post handle args'
        if 'post_type' in data_dict:
            o.post_type = data_dict['post_type']
            data_dict.pop('post_type')
        if 'demisauce_id' in data_dict:
            o.person_id = int(data_dict['demisauce_id'])
            data_dict.pop('demisauce_id')
            p = Person.get(self.site.id,o.person_id)
            o.displayname = p.displayname
        return data_dict
    
    def posts(self,q=None):
        if not q:
            logging.debug("In posts.q limit = %s" % self.limit)
            qry = self.db.session.query(Object).filter(Object.post_type=='post').options(eagerload('person')).limit(self.limit)
            if self.start > 0:
                logging.debug("self.start = %s" % self.start)
                qry = qry.offset(self.start)
        else:
            qry = self.db.session.query(self.__class__.object_cls).filter(
                    self.__class__.object_cls.name.like('%' + q + '%'))
        self.qry = qry
    
    def action_get_list(self,q=None):
        if not q:
            logging.debug("In list.q limit = %s" % self.limit)
            qry = self.db.session.query(Object).options(eagerload('person')).limit(self.limit)
            if self.start > 0:
                logging.debug("self.start = %s" % self.start)
                qry = qry.offset(self.start)
        else:
            qry = self.db.session.query(self.__class__.object_cls).filter(
                    self.__class__.object_cls.name.like('%' + q + '%'))
        self.qry = qry
    
    def json_formatter(self,o):
        if o:
            output = o.to_dict()
            return output
        return None
    
    def action_get_object(self,id, data_dict = {}):
        if isinstance(id,int) and self.id > 0:
            self.object = Object.saget(id)  
        elif isinstance(id,int) and self.id == 0:
            pass
        else:
            logging.debug("calling by_slug = %s" % (id))
            self.object = Object.by_slug(site_id=self.site.id,slug=id)  
        
        logging.debug('METHOD: %s' % dir(self.request))
        if self.object:
            self.qry = [self.object]
        elif self.request.method in ('POST','PUT','DELETE'):
            self.qry = []
        elif self.request.method == 'GET':
            self.set_status(404)
            logging.error("no object %s" % self.id)
    

class GroupApiHandler(ApiSecureHandler):
    object_cls = Group
    def action_get_object(self,id, data_dict = {}):
        if type(id) == int:
            self.object = Group.get(site_id=self.site.id,id=id) 
        else:
            self.object = Group.by_slug(site_id=self.site.id,slug=id)  
        if self.object:
            self.qry = [self.object]
        else:
            logging.error("no Group %s" % self.id)
    
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
            output = o.to_dict(keys=['name','slug','id','url'])
            if o.members:
                members = []
                for m in o.members:
                    members.append(m.to_dict(keys=['displayname','email','id']))
                output['members'] = members
            return output
        return None
    
    def action_get_list(self,q=None):
        if q:
            qry = self.db.session.query(Group).filter(and_(
                Group.name.like('%' + q + '%'),Email.site_id==self.site.id))
        else:
            qry = self.db.session.query(Group).filter(Email.site_id==self.site.id)
            logging.debug("in group list, qry = %s" % qry)
        self.qry = qry
    

class HookApiHandler(BaseHandler):
    def _do_proxy(self,*args,**kwargs):
        logging.debug("PROXY %s *args, **kwargs = %s, %s" % (kwargs['method'],args,kwargs))
        logging.debug("PROXY %s %s, body=%s" % (kwargs['method'],self.request.arguments,self.request.body))
        http = tornado.httpclient.HTTPClient()
        response = http.fetch("http://192.168.1.43/blog/xmlrpc.php",
            method=kwargs['method'],
            headers=self.request.headers, 
            body=self.request.body)
        logging.debug(str(response))
        self.write(response.body)
    
    def get(self,*args):
        logging.debug("HOOK?PROXY GET *args, **kwargs = %s" % (str(args)))
        if args and len(args) > 0 and 'proxy' == args[0]:
            self._do_proxy(*args,method='GET')
        else:
            pass
    
    def post(self,*args):
        if args and len(args) > 0 and 'proxy' == args[0]:
            self._do_proxy(*args,method="POST")
        else:
            logging.debug("POST %s" % self.request.arguments)
        
    



""" GET  : get
    POST : add/update
    DELETE: delete
    
    /api/noun/id/(action|filter|property)
    
    (r"/api/(.*?)/([0-9]*?|.*?|all|list)/(.*?)(?:\.)?(json|xml|custom)?", ApiSecureHandler),
    (r"/api/(.*?)/([0-9]*?|.*?|all|list)(.json|.xml|.custom)?", ApiSimpleHandler),
"""
_controllers = [
    (r"/api/(hook|webhook)(?:\/)?(.*?)",HookApiHandler), 
    (r"/api/(tbdproxy|proxy)/(.*?)",HookApiHandler), 
    (r"/api/(activity)/(.*?)", ActivityApiHandler),
    (r"/api/(user|person)/(.*?)/(init_user|tbdmorestuff)", PersonAnonApi),
    (r"/api/(user|person)/([0-9]*?|.*?)/(.*?).(json|xml|custom)?", PersonApiHandler),
    (r"/api/(user|person)/(.*?).(?:json|xml|custom)", PersonApiHandler),
    (r"/api/(user|person)/(.*?)", PersonApiHandler),
    (r"/api/(group)/([0-9]*?|.*?)/(.*?).(json|xml|custom)?", GroupApiHandler),
    (r"/api/(group)/(.*?).(?:json|xml|custom)", GroupApiHandler),
    (r"/api/(group)/(.*?)", GroupApiHandler),
    (r"/api/(site)/([0-9]*?|.*?|all|list)/(.*?)(?:\.)?(json|xml|custom)?", SiteApiHandler),
    (r"/api/(site)/(.*?)(.json|.xml|.custom)", SiteApiHandler),
    (r"/api/(app)/([0-9]*?|.*?|all|list)/(.*?)(?:\.)?(json|xml|custom)?", AppApiHandler),
    (r"/api/(app)/(.*?)(.json|.xml|.custom)", AppApiHandler),
    (r"/api/(email)/([0-9]*?|.*?|all|list)/(.*?)(?:\.)?(json|xml|custom)?", EmailApiHandler),
    (r"/api/(email)/(.*?)(.json|.xml|.custom)", EmailApiHandler),
    (r"/api/(service)/([0-9]*?|.*?|all|list)/(.*?)(?:\.)?(json|xml|custom)?", ServiceApiHandler),
    (r"/api/(service)/(.*?)(?:.json|.xml|.custom)", ServiceApiHandler),
    (r"/api/(object)/([0-9]*?|.*?|all|list)/(.*?)(?:\.)?(json|xml|custom)?", ObjectApiHandler),
    (r"/api/(object)/(.*?)(?:.json|.xml|.custom)", ObjectApiHandler),
]

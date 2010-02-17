import urllib, urllib2, os, sys, logging
import string
import httpfetch
from tornado.options import options,define
define("site_root", default="/home/demisauce", help="Root Path of site, set at runtime")
define("redis_host", default="127.0.0.1",help="List of redis hosts:  192.168.1.1:5555,etc",multiple=False)
define("gearman_servers",default=["127.0.0.1"],multiple=True,help="gearman hosts format host:port,host:port")
define("solr_server",default="http://127.0.0.1:8080/dssolr",help="http url and path of solr server")
define("asset_url",default="http://assets.yourdomain.com", help="fq url to asset address")
define("demisauce_url",default="http://localhost:4950", help="path to demisauce server")
define("demisauce_api_key",default="5c427992131479acb17bcd3e1069e679",help="api key")
define("demisauce_admin",default="demisauce@demisauce.org",help='email address of demisauce admin')

define("memcached_servers", default=["127.0.0.1:11211"],multiple=True, help="list of memcached servers")
define("demisauce_cache", default="memcache", 
        help="type of cache (memcache|pylons|gae|django|redis|dummy)")

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # for GAE
        from django.utils import simplejson as json
from datetime import datetime
from demisaucepy.service import ServiceDefinition, ServiceClient, \
    RetrievalError, args_substitute, SUCCESS_STATUS

import demisaucepy.cache_setup
import hashlib
import warnings
import xmlrpclib
import re
import tornado
from tornado.options import options, define

log = logging.getLogger(__name__)

__version__ = '0.1.1'


DATETIME_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(\.\d+)?Z$')



def hash_email(email):
    return hashlib.md5(email.lower()).hexdigest()

def demisauce_ws_get(noun,resource_id,data={},format='json',extra_headers={},qs={},api_key=None,cache=True):
    return demisauce_ws(noun,resource_id,action='get',data=data,api_key=api_key,
                format=format,extra_headers=extra_headers,qs=qs,cache=cache)


def demisauce_ws(noun,resource_id,action=None,data={},format='json',apikey=None,servicedef=None,
        extra_headers={},load_def=False,app='demisauce',http_method='GET',qs={},cache=False,cache_time=900):
    """Core web service get
    
    api/noun/id/action.format?apikey={yourkey}&q=query-or-search-parameters
    api/noun/id/selector.format
    api/noun/id.format?apikey=yourapikey
        
    examples:
        - api/service/email.json?apikey=myapikey
        - api/service/list.json?apikey=myapikey
        - api/email/welcomemessage?apikey=myapikey
        - api/person/1234.json?apikey
    
    Semi Restful operations (create/read/update/delete)
        - (post=add/update, get=read, delete=delete)
    returns
    """
    servicedef = ServiceDefinition(
        name=noun,
        format=format,
        app_slug=app,
        cache=cache,
        api_key=apikey,
        cache_time=cache_time
    )
    servicedef.isdefined = False if load_def else True
    client = ServiceClient(service=servicedef)
    client.use_cache = cache
    client.extra_headers = extra_headers
    if action:
        resource_id = '%s/%s' % (resource_id,action)
    response = client.fetch_service(request=resource_id,data=data,http_method=http_method,qs=qs)
    return response


class jsonwrapper(dict):
    def __init__(self,jsonval=None):
        self._index = 0
        self._id_field = 'id'
        self._json_list = []
        self._json_dict = {}
        if jsonval:
            self._load(jsonval)
    
    def _load(self,jsonval):
        if isinstance(jsonval,str):
            jsonval = json.loads(jsonval)
        if isinstance(jsonval,dict):
            self._json_dict = jsonval
        elif isinstance(jsonval,list):
            self._json_list = jsonval
            if len(jsonval) == 1:
                self._json_dict = jsonval[0]
        else:
            return
            #raise Exception("how can it be none list, dict?")
        if self._json_list:
            self._index = len(self._json_list)
    
    def __iter__(self):
        return self
    
    def next(self):
        if self._index == 0:
            if self._json_list:
                self._index = len(self._json_list)
            raise StopIteration
        self._index = self._index - 1
        val = self._json_list[self._index]
        return self._to_python(val)
    
    def __len__(self):
        if self._json_list:
            return len(self._json_list)
        elif self._json_dict:
            return len(self._json_dict)
        return 0
    
    def __setattr__(self,name,value):
        if name[:1] == '_':
            self.__dict__[name] = value
        elif isinstance(value,dict):
            self._json_dict[name] = jsonwrapper(value)
        else:
            self._json_dict[name] = value
    
    def __getattr__(self, name):
        if self._json_dict:
            if name in self._json_dict:
                return self._to_python(self._json_dict[name],name)
            elif ('datetime_%s' % name) in self._json_dict:
                val = self._json_dict['datetime_%s' % name]
                return datetime.fromtimestamp(float(val))
            elif 'extra_json' in self._json_dict and self._json_dict['extra_json'] \
                and name in self._json_dict['extra_json']:
                return self._json_dict['extra_json'][name]
        return None
    
    def __getitem__(self, name):
        if isinstance(name,int) and self._json_list:
            val = self._json_list[name]
        elif isinstance(name,str) and self._json_dict:
            if name in self._json_dict:
                val = self._json_dict[name]
            elif 'datetime_%s' % name in self._json_dict:
                val = self._json_dict['datetime_%s' % name]
                return datetime.fromtimestamp(float(val))
            else:
                return None
        
        return self._to_python(val,name)
    
    def to_form_data(self):
        out = {}
        for k,v in self._json_dict.items():
            if isinstance(v,jsonwrapper):
                out[k] = json.dumps(v.to_form_data())
            elif isinstance(v,(dict)):
                out[k] = json.dumps(v)
            else:
                out[k] = v
        return out
    
    def _to_python(self,val,key=None):
        if val is None:
            return val
        if isinstance(val, (int, float, long, complex)) and key and key.find('datetime_') == 0:
            val = datetime.fromtimestamp(float(val))
            return val
                
        if isinstance(val, (int, float, long, complex)):
            return val
        
        if isinstance(val,jsonwrapper):
            return val
            raise Exception('here it is')
        elif isinstance(val,dict):
            return jsonwrapper(val)
        elif isinstance(val, (list)):
            return jsonwrapper(val)
        elif isinstance(val,(tuple)):
            return val
        
        if val == 'true':
            return True
        elif val == 'false':
            return False
        
        if isinstance(val, basestring):
            possible_datetime = DATETIME_REGEX.search(val)
            
            if possible_datetime:
                date_values = possible_datetime.groupdict()
                
                for dk, dv in date_values.items():
                    date_values[dk] = int(dv)
                
                return datetime(date_values['year'], date_values['month'], date_values['day'], date_values['hour'], date_values['minute'], date_values['second'])
        
        # else, probably string?
        return val
    
    def _from_python(self, value):
        """
        Converts python values to a form suitable for insertion into the xml
        we send to solr.
        """
        if isinstance(value, datetime):
            value = value.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif isinstance(value, date):
            value = value.strftime('%Y-%m-%dT00:00:00Z')
        elif isinstance(value, bool):
            if value:
                value = 'true'
            else:
                value = 'false'
        else:
            value = unicode(value)
        return value
    
    def _to_pythonOLD(self, value):
        """
        Converts values from Solr to native Python values.
        """
        if isinstance(value, (int, float, long, complex)):
            return value
        
        if isinstance(value, (list, tuple)):
            value = value[0]
        
        if value == 'true':
            return True
        elif value == 'false':
            return False
        
        if isinstance(value, basestring):
            possible_datetime = DATETIME_REGEX.search(value)
        
            if possible_datetime:
                date_values = possible_datetime.groupdict()
            
                for dk, dv in date_values.items():
                    date_values[dk] = int(dv)
            
                return datetime(date_values['year'], date_values['month'], date_values['day'], date_values['hour'], date_values['minute'], date_values['second'])
        
        try:
            # This is slightly gross but it's hard to tell otherwise what the
            # string's original type might have been. Be careful who you trust.
            converted_value = eval(value)
            
            # Try to handle most built-in types.
            if isinstance(converted_value, (list, tuple, set, dict, int, float, long, complex)):
                return converted_value
        except:
            # If it fails (SyntaxError or its ilk) or we don't trust it,
            # continue on.
            pass
        
        return value
    


class RemoteObject(jsonwrapper):
    'chainable remote object'
    service = 'tbd'
    id_field = 'id'
    def __init__(self,*args,**kwargs):
        if 'apikey' in kwargs:
            self._apikey = kwargs['apikey']
            kwargs.pop('apikey')
        else:
            self._apikey = None
        if len(args) > 0 and isinstance(args[0],dict):
            super(RemoteObject, self).__init__(args[0])
        elif kwargs and isinstance(kwargs,dict):
            super(RemoteObject, self).__init__(kwargs)
        else:
            super(RemoteObject, self).__init__()
    
    @property
    def _service(self):
        return self.__class__.service
    
    @property
    def _id(self):
        if hasattr(self,self._id_field):
            return str(self[self._id_field])
        raise Exception("no id field found")
    
    @classmethod
    def GET(cls,id=0,action=None,limit=None,cache=True):
        s = cls()
        s._get_method(id=id,action=action,limit=limit,cache=cache)
        log.debug('GET id=%s for %s, status=%s' % (id,s._service,s._response.status))
        if s._response.success and s._response.status in SUCCESS_STATUS:
            return s
        else:
            log.debug('not found id=%s for %s' % (id,s._service))
            return None
    
    def get(self,id=0,action=None,limit=None,cache=True):
        self._get_method(id=id,action=action,limit=limit,cache=cache)
        return self
    
    def _get_method(self,id=0,action=None,limit=None,cache=True):
        qs = {} if not limit else {'limit':limit}
        self._response = demisauce_ws(self._service,str(id),action,qs=qs,
            cache=cache,apikey=self._apikey)
        if self._response.success and self._response.status in SUCCESS_STATUS:
            #log.debug("RESPONSE.STATUS = %s, %s" % (self._response.status,self._response.json))
            self._load(self._response.json)
    
    def POST(self,id=0, data={},action=None,service=None):
        id = self.id if (id == 0 and self.id > 0) else id
        log.debug("doing POST: service=%s, id=%s, action=%s" % (self._service,id,action))
        if len(data) > 0:
            self._response = demisauce_ws(self._service,id,action,data=data,
                http_method='POST',apikey=self._apikey)
        elif self._json_list and len(self._json_list > 0):
            self._response = demisauce_ws(self._service,id,action,http_method='POST',
                data=json.dumps(self._json_list),apikey=self._apikey)
        else:
            self._response = demisauce_ws(self._service,id,action,data=self.to_form_data(),
                http_method='POST',apikey=self._apikey)
        if self._response.success and self._response.status in SUCCESS_STATUS:
            self._load(self._response.body)
        else:
            log.info("FAILED POST: service=%s, id=%s, action=%s" % (self._service,id,action))
    
    def PUT(self,data={}):
        action = None
        if len(data) > 0:
            self._response = demisauce_ws(self._service,self._id,action,
                    data=json.dumps(data),http_method='PUT',apikey=self._apikey)
        else:
            self._response = demisauce_ws(self._service,self._id,action,http_method='PUT',
                            data=json.dumps(self._json_dict),apikey=self._apikey)
        if self._response.success and self._response.status in SUCCESS_STATUS:
            self._load(self._response.json)
    
    def DELETE(self):
        self._response = demisauce_ws(self._service,str(self.id),
            http_method="DELETE",apikey=self._apikey)
    
class DSUser(RemoteObject):
    service = 'person'

class Service(RemoteObject):
    service = 'service'

class App(RemoteObject):
    service = 'app'

class Email(RemoteObject):
    service = 'email'

class Activity(RemoteObject):
    service = 'activity'

class Object(RemoteObject):
    service = 'object'

class Site(RemoteObject):
    service = 'site'
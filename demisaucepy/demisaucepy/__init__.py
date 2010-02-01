import urllib, urllib2, os, sys, logging
import string
import httpfetch
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # for GAE
        from django.utils import simplejson as json
import datetime
from demisaucepy.service import ServiceDefinition, ServiceClient, \
    RetrievalError, args_substitute, SUCCESS_STATUS
from tornado.options import options,define
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

def hash_email(email):
    return hashlib.md5(email.lower()).hexdigest()

def demisauce_ws_get(noun,resource_id,data={},format='json',extra_headers={},api_key=None,cache=True):
    return demisauce_ws(noun,resource_id,action='get',data=data,api_key=api_key,
                format=format,extra_headers=extra_headers,cache=cache)


def demisauce_ws(noun,resource_id,action=None,data={},format='json',api_key=None,servicedef=None,
        extra_headers={},app='demisauce',http_method='GET',cache=True,cache_time=900):
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
        api_key=api_key,
        cache_time=cache_time
    )
    
    client = ServiceClient(service=servicedef)
    client.use_cache = cache
    client.extra_headers = extra_headers
    if action:
        resource_id = '%s/%s' % (resource_id,action)
    response = client.fetch_service(request=resource_id,data=data,http_method=http_method)
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
            raise Exception("how can it be none list, dict?")
        if self._json_list:
            self._index = len(self._json_list)
    
    def __iter__(self):
        return self
    
    def next(self):
        if self._index == 0:
            raise StopIteration
        self._index = self._index - 1
        val = self._json_list[self.index]
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
        else:
            self._json_dict[name] = value
            print("setattr: n,v = %s, %s" % (name,value))
    
    def __getattr__(self, name):
        if self._json_dict:
            logging.debug("getting %s from keys = %s" % (name,self._json_dict.keys()))
            val = self._json_dict[name]
            return self._to_python(val)
        else:
            raise KeyError
    
    def __getitem__(self, name):
        if isinstance(name,int) and self._json_list:
            val = self._json_list[name]
        elif isinstance(name,str) and self._json_dict:
            val = self._json_dict[name]
        else:
            raise KeyError
        
        return self._to_python(val)
    
    def _to_python(self,val):
        if val is None:
            return val
        
        if isinstance(val, (int, float, long, complex)):
            return val
        
        if isinstance(val,dict):
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
    service = 'tbd'
    id_field = 'id'
    def __init__(self,*args,**kwargs):
        #print('service = %s' % self.__class__.service)
        #print('kwargs typeof = %s   && args = %s, len(args) %s' % (type(kwargs), args, len(args)) )
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
    def GET(cls,id=0,action=None):
        s = cls()
        s._get_method(id=id,action=action)
        if s._response.success and s._response.status in SUCCESS_STATUS:
            return s
        else:
            return None
    
    def _get_method(self,id=0,action=None):
        self._response = demisauce_ws(self._service,str(id),action,data={})
        if self._response.success and self._response.status in SUCCESS_STATUS:
            self._load(self._response.json)
    
    def POST(self,data={},action=None):
        if len(data) > 0:
            self._response = demisauce_ws(self._service,'0',action,
                    data=data,http_method='POST')
        elif self._json_list and len(self._json_list > 0):
            self._response = demisauce_ws(self._service,'0',action,
                data=json.dumps(self._user_list),http_method='POST')
        else:
            self._response = demisauce_ws(self._service,'0',action,
                            data=self._json_dict,http_method='POST')
        if self._response.success and self._response.status in SUCCESS_STATUS:
            self._load(self._response.data)
    
    def PUT(self,data={}):
        action = None
        if len(data) > 0:
            self._response = demisauce_ws(self._service,self._id,action,
                    data=json.dumps(data),http_method='PUT')
        else:
            self._response = demisauce_ws(self._service,self._id,action,
                            data=json.dumps(self._json_dict),http_method='PUT')
        if self._response.success and self._response.status in SUCCESS_STATUS:
            self._load(self._response.json)
    
    def DELETE(self):
        self._response = demisauce_ws(self._service,str(self.id),http_method="DELETE")
    

class Service(RemoteObject):
    service = 'service'

class Email(RemoteObject):
    service = 'email'
    
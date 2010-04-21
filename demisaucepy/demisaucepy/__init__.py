import urllib, urllib2, os, sys, logging
import string
import httpfetch
from tornado.options import options,define
from demisaucepy import options as dsoptions

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
from demisaucepy.serializer import JsonSerializer, AvroSchemaSerializer, \
    get_schema
import demisaucepy.cache_setup
import hashlib
import warnings
import xmlrpclib
import re
import tornado
from tornado.options import options, define

log = logging.getLogger("demisaucepy")

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


class objectwrapper(dict):
    serializer = JsonSerializer() # 
    def __init__(self,*args,**kwargs):
        self._index = 0
        dataval = None
        self._list = []
        self._fields = {}
        if 'serializer' in kwargs:
            self._serializer = kwargs['serializer']
            kwargs.pop("serializer")
        else:
            self._serializer = self.__class__.serializer
        if len(args) > 0 and isinstance(args[0],(dict,list)):
            dataval = args[0]
        elif kwargs and isinstance(kwargs,dict):
            dataval = kwargs
        elif len(args) == 1:
            dataval = args[0]
        if dataval: 
            self._load(dataval)
    
    def _load(self,dataval):
        if not isinstance(dataval,(list,dict)):
            #log.debug("type=%s, serializer=%s" %(type(dataval),self._serializer.__class__))
            dataval = self._serializer.to_python(dataval)
        if isinstance(dataval,dict):
            self._fields = dataval
        elif isinstance(dataval,list):
            self._list = dataval
            if len(dataval) == 1:
                self._fields = dataval[0]
        else:
            raise Exception("how can it be none list, dict? %s" % (type(dataval)))
            return
        if self._list:
            self._index = len(self._list)
    
    def __iter__(self):
        return self
    
    def append(self,obj):
        if not self._list:
            self._list = []
        self._list.append(obj)
    
    def next(self):
        if self._index == 0:
            if self._list:
                self._index = len(self._list)
            raise StopIteration
        self._index = self._index - 1
        val = self._list[self._index]
        return self._to_python(val)
    
    def __len__(self):
        if self._list:
            return len(self._list)
        elif self._fields:
            return len(self._fields)
        return 0
    
    def __setattr__(self,name,value):
        if name[:1] == '_':
            self.__dict__[name] = value
        elif isinstance(value,(list,dict)):
            self._fields[name] = objectwrapper(value)
        else:
            self._fields[name] = value
    
    def __getattr__(self, name):
        if self._fields:
            if name in self._fields:
                val = self._to_python(self._fields[name],name)
                #log.debug('getting name=%s, val=%s, type=%s' % (name,val,type(val)))
                return val
            elif ('datetime_%s' % name) in self._fields:
                val = self._fields['datetime_%s' % name]
                return datetime.fromtimestamp(float(val))
            elif 'extra_json' in self._fields and self._fields['extra_json'] \
                and name in self._fields['extra_json']:
                return self._fields['extra_json'][name]
        #if name in self.__dict__:
        #    return self.__dict__[name]
        #log.debug('in get attr %s' % (name))
        return None
    
    def __getitem__(self, name):
        if isinstance(name,int) and self._list:
            val = self._list[name]
        elif isinstance(name,str) and self._fields:
            if name in self._fields:
                val = self._fields[name]
            elif 'datetime_%s' % name in self._fields:
                val = self._fields['datetime_%s' % name]
                return datetime.fromtimestamp(float(val))
            else:
                return None
        
        return self._to_python(val,name)
    
    def dict_to_python(self,d):
        out = {}
        for k,v in d.items():
            if isinstance(v,objectwrapper):
                out[k] = v.to_python()
            else:
                out[k] = v
        return out
    
    def to_python(self):
        if self._list and (len(self._list) > 1 or (len(self._list) == 1 and self._fields == {})):
            out = []
            for li in self._list:
                #assert type(li) is objectwrapper
                if not type(li) is objectwrapper:
                    #log.debug('not objectwrapper? %s' % li)
                    out.append(li)
                else:
                    out.append(li.to_python())
            return out
        #if self._list and len(self._list) == 1:
        #    return self.dict_to_python(self._list[0])
        #else:
        return self.dict_to_python(self._fields)
    
    def is_complex(self,data=None):
        """detemines if this dictionary whoose fields 
            contain lists/dicts, if so it is complex"""
        is_complex = False
        assert isinstance(data,(dict))
        for k,v in data.items():
            if isinstance(v,(objectwrapper,list,dict)):
                is_complex = True
                break
        return is_complex
    
    def to_form_data(self,data=None):
        """Returns A dictionary of simple name/value pairs OR returns a single 
        json string if format is too complex"""
        if data:
            if self.is_complex(data=data):
                return json.dumps(data)
            return data
        if self._list and len(self._list) > 1:
            return json.dumps(self.to_python())
        elif self.is_complex(data=self._fields):
            #log.debug("is complex so returning json.dumps of %s" % json.dumps(self.to_python()))
            return json.dumps(self.to_python())
        else:
            #log.debug("not complex %s" % (self.to_python()))
            return self.to_python()
    
    def to_format(self):
        return self._serializer.to_format(self.to_python())
    
    def _to_python(self,val,key=None):
        if val is None:
            return val
        if isinstance(val, (int, float, long, complex)) and key and key.find('datetime_') == 0:
            val = datetime.fromtimestamp(float(val))
            return val
                
        if isinstance(val, (int, float, long, complex)):
            return val
        
        if isinstance(val,objectwrapper):
            return val
        elif isinstance(val,dict):
            return objectwrapper(val)
        elif isinstance(val, (list)):
            is_complex = False
            for item in val:
                if isinstance(item,(list,dict)):
                    is_complex = True
                    break
            if is_complex:
                return objectwrapper(val)
            else:
                return val
        elif isinstance(val,(tuple)):
            return val
        
        if val in ('true','True'):
            return True
        elif val in ('false','False'):
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
    


class RemoteObject(objectwrapper):
    'remote object'
    service = 'tbd'
    id_field = 'id'
    def __init__(self,*args,**kwargs):
        if 'apikey' in kwargs:
            self._apikey = kwargs['apikey']
            kwargs.pop('apikey')
        else:
            self._apikey = None
        super(RemoteObject, self).__init__(*args,**kwargs)
    
    @property
    def _service(self):
        return self.__class__.service
    
    @property
    def _id(self):
        if hasattr(self,self.__class__.id_field):
            return str(getattr(self,self.__class__.id_field))
        raise Exception("no id field found")
    
    @classmethod
    def GET(cls,id=0,action=None,limit=None,cache=True):
        s = cls()
        id = str(id)
        s._get_method(id=id,action=action,limit=limit,cache=cache)
        #log.debug('GET id=%s for %s, status=%s' % (id,s._service,s._response.status))
        #log.debug('GET id=%s for %s, status=%s' % (id,s._service,s._response.json))
        if s._response.success and s._response.status in SUCCESS_STATUS:
            return s
        else:
            #log.debug('not found id=%s for %s' % (id,s._service))
            if id in ('list'):
                return []
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
            if not self._response.json in (None,''):
                self._load(self._response.json)
            else:
                return None
        
    
    def POST(self,id=0, data={},action=None,service=None):
        id = self.id if (id == 0 and self.id > 0) else id
        #log.debug("doing POST: service=%s, id=%s, action=%s" % (self._service,id,action))
        #log.debug("doing POST: service=%s, id=%s, action=%s, data=%s" % (self._service,id,action,data))
        if data and len(data) > 0:
            data = self.to_form_data(data=data)
        else:
            data = self.to_form_data()
        #log.debug('data = %s' % (data))
        self._response = demisauce_ws(self._service,id,action,data=data,
                http_method='POST',apikey=self._apikey)
        if self._response.success and self._response.status in SUCCESS_STATUS:
            #log.debug(self._response.json)
            self._load(self._response.json)
        else:
            log.info("FAILED POST: service=%s, id=%s, action=%s" % (self._service,id,action))
    
    def PUT(self,data={}):
        action = None
        if len(data) > 0:
            data = json.dumps(data)
        else:
            data = json.dumps(self.to_python())
        
        self._response = demisauce_ws(self._service,self._id,action,
                    data=data,http_method='PUT',apikey=self._apikey)
        if self._response.success and self._response.status in SUCCESS_STATUS:
            #log.debug("type = %s, json =%s" % (type(self._response.json),self._response.json))
            self._load(self._response.json)
        else:
            log.error("???? error  %s" % self._response.body)
    
    def DELETE(self):
        self._response = demisauce_ws(self._service,str(self.id),
            http_method="DELETE",apikey=self._apikey)
    

class DSUser(RemoteObject):
    service = 'person'
    def bool_setattr(self,name,value,obj_type):
        if not value and self.get_attribute(name):
            if not self.delete_attributes:
                self.delete_attributes = []
            self.delete_attributes.append({'name':name})
        elif value and not self.get_attribute(name):
            if not self.attributes:
                self.attributes = []
            self.attributes.append({'name':name,'value':True,'object_type':obj_type})
    
    def get_attribute(self,name):
        """Returns the UserAttribute object for given name"""
        if not self.attributes:
            return None
        for attribute in self.attributes:
            if attribute.name == name:
                if attribute.encoding == 'json' and isinstance(attribute.value,(str,unicode)):
                    attribute.value = json.loads(attribute.value)
                return attribute
        return None
    
    def get_val(self,name):
        attr = self.get_attribute(name)
        if attr:
            return attr.value
        return None
    
    def has_attribute(self,name):
        """Returns True/False if it has given key attribute"""
        if not self.attributes:
            return None
        for attribute in self.attributes:
            if attribute.name == name:
                return True
        return False
    
    def has_attribute_value(self,name,value):
        """Returns True/False if it has given key/value pair attribute"""
        if not self.attributes:
            return False
        for attribute in self.attributes:
            if attribute.name == name and value == attribute.value:
                return True
        return False
    

class DSGroup(RemoteObject):
    service = 'group'

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

class Content(RemoteObject):
    service = 'content'

site_schema = get_schema('site')
class Site(RemoteObject):
    service = 'site'
    avroschema = site_schema
    serializer = JsonSerializer(site_schema)
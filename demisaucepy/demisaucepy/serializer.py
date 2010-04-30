import sys, logging, os, re, time, datetime
from datetime import datetime as dt
import avro
from avro import schema
from avro import io
from avro import datafile
import cStringIO
from binascii import hexlify
try:
    import json
except ImportError:
    import simplejson as json

log = logging.getLogger("demisaucepy")

class DSSerializer(object): 
    """base class interface for serializers, which take entity class/objects
        and serialize them to some storable and transportable format
    """
    def __init__(self,schema=None):
        self._schema = schema
    
    def move_extras(self,py_data,depth=0):
        'finds extra fields and puts them in extra storage'
        if isinstance(py_data,dict):
            extra = {}
            for k in py_data.keys():
                if not self.has_field(k):
                    extra[k] = py_data[k]
                    py_data.pop(k)
            if len(extra)> 0:
                py_data['extra'] = json.dumps(extra)
        elif isinstance(py_data,list) and depth == 0:
            for li in py_data:
                li = self.move_extras(li,depth=1)
        else:
            raise Exception("Data needs to be of list/dict type")
        return py_data
    
    def move_extras_back(self,py_data):
        if 'extra' in py_data:
            extras = json.loads(py_data['extra'])
            for k in extras.keys():
                py_data[k] = extras[k]
    
    def to_python(self,dataval):
        raise NotImplemented("Not implemented")
    

def is_json(val):
    if val and isinstance(val,(str,unicode)) and len(val) > 2:
        if (val.find("{") > -1 and val.find("{") < 3) or \
            (val.find("[") > -1 and val.find("[") < 3):
            return True
    return False

class SerializationMixin(object):
    _ignore_keys = []
    _readonly_keys = []
    _allowed_api_keys = []
    __all_schema_keys__ = None
    def get_keys(self):
        if hasattr(self,"_fields"):
            return self._fields.keys()
        return []
    
    def get_ignore_keys(self):
        if hasattr(self.__class__,"_ignore_keys"):
            return self.__class__._ignore_keys
        return []
    
    def get_readonly_keys(self):
        return self.__class__._readonly_keys
    
    def to_dict(self,keys=None):
        """
        serializes to dictionary, converting non serializeable fields
            to some other format or ignoring them.  
        :_ignore_keys: which fields to ignore and not serialize
        :_readonly_keys: which fields to read, but not write
        :_allowed_api_keys:  which fields to allow from api
        :__all_schema_keys__: list of all fields of this obj
        """
        # cs = time.mktime(self.created.timetuple()) # convert to seconds
        # to get back:  datetime.datetime.fromtimestamp(cs)
        dout = {}
        ignore_keys = []
        
        if not keys:
            keys = self.get_keys()
        
        ignore_keys = self.get_ignore_keys()
        
        for key in keys:
            if key not in ignore_keys and key.find("_") != 0 and hasattr(self,key):
                attr = getattr(self,key)
                if type(attr) == datetime or type(attr) == datetime.datetime:
                    dout.update({u'datetime_%s' % key:time.mktime(attr.timetuple())})
                elif key.find('json') >= 0:
                    if attr in [None,'']:
                        dout.update({key:attr})
                    else:
                        # mysql escapes wrong?
                        #attr = attr.replace("'","\"")
                        dout.update({key:json.loads(attr)})
                elif type(attr) == str:
                    dout.update({key:attr})
                else:
                    dout.update({key:attr})
        
        return dout
    
    def to_json(self,keys=None):
        return json.dumps(self.to_dict(keys=keys))
    
    def from_dict(self,py_dict,allowed_keys=None):
        """
        Chainable - Converts from an encoded python dictionary
        back to a populated object::
            
            peep = Person().from_dict(json_dict)
        
        """
        if not allowed_keys:
            keys = self.get_keys()
        else:
            keys = allowed_keys
        rokeys = self.get_readonly_keys()
        
        json_key = 'extra_json'
        json_attr = None
        extra_json = {}
        self._json = py_dict # save decoded json
        for key in py_dict:
            if key in keys or key.find('datetime') >= 0:
                if key.find('json') >= 0:
                    json_key = key
                    #log.debug('jsonkey=%s type=%s' % (key,type(py_dict[key])))
                    if py_dict[key] in(None,'None','null'):
                        pass
                    elif isinstance(py_dict[key],(str,unicode)):
                        log.debug(py_dict[key])
                        extra_json.update(json.loads(py_dict[key]))
                    else:
                        extra_json.update(py_dict[key])
                elif key.find('datetime_') == 0:
                    setattr(self,key[9:],dt.fromtimestamp(float(py_dict[key])))
                else:
                    setattr(self,key,self._to_python(py_dict[key]))
            elif not key in rokeys:
                #log.debug('key = %s   keys = %s' % (key,str(keys)))
                extra_json.update({key:self._to_python(py_dict[key])})
        
        if len(extra_json) > 0 and 'apikey' in extra_json:
            extra_json.pop('apikey')
        if len(extra_json) > 0:
            #log.debug("json_key=%s" % json_key)
            if hasattr(self,json_key):
                json_attr = getattr(self,json_key)
            if json_attr and isinstance(json_attr,dict):
                setattr(self,json_key, json_attr.update(extra_json))
            elif json_attr and isinstance(json_attr,(str,unicode)):
                #log.debug(json_attr)
                tmpjson = json.loads(json_attr)
                tmpjson.update(extra_json)
                setattr(self,json_key, tmpjson)
            elif hasattr(self,json_key) and json_attr == None:
                setattr(self,json_key, extra_json)
            else:
                log.error("type = , val=%s" % (extra_json))
        elif len(extra_json) == 0:
            setattr(self,json_key, None)
        return self
    
    def from_json(self,json_string):
        """
        Chainable - Converts from a json string back to a populated object::
            
            peep = Person().from_json(json_string)
        
        """
        self.from_dict(json.loads(json_string))
        return self
    
    def _to_python(self,val):
        if val is None:
            return val
        
        if isinstance(val, (int, float, long, complex)):
            return val
        if val in (u'none',u'None','none','None'):
            return None
        
        if val in ('true',u'true','True',u'True'):
            return True
        elif val in ('false',u'false','False',u'False'):
            return False
        #elif isinstance(val,(str,unicode)) and val.find("{") == 0 or val.find("[") == 0:
        #    # is json?
        #    return json.loads(val)
        # else, probably string?
        return val
    

class JsonSerializer(DSSerializer): 
    def to_python(self,dataval):
        if dataval in ('',None):
            return
        assert isinstance(dataval,(str,unicode)), "Must be instance of string"
        return json.loads(dataval)
    

class AvroSchemaSerializer(DSSerializer):
    def has_field(self,name):
        if not hasattr(self,"_field_names"):
            self._field_names = [field.name for field in self._schema.fields]
        return name in self._field_names
    
    def to_format(self, py_data):
        "serializes to avro data from python"
        if not hasattr(self,'_writer'):
            self._writer = None
        self._writer = cStringIO.StringIO()
        encoder = io.BinaryEncoder(self._writer)
        datum_writer = io.DatumWriter(self._schema)
        datum_writer.write(self.move_extras(py_data), encoder)
        return self._writer.getvalue()
    
    def to_python(self,dataval):
        py_data = self.from_avro(dataval)
        self.move_extras_back(py_data)
        return py_data
    
    def from_avro(self, avrodata, readers_schema=None):
        #self.write_datum(data)
        reader = cStringIO.StringIO(avrodata)
        decoder = io.BinaryDecoder(reader)
        datum_reader = io.DatumReader(self._schema, readers_schema)
        return datum_reader.read(decoder)
    

# read data in binary from file
TEST_ROOT = os.path.dirname(os.path.realpath(__file__))
def get_schema(name):
    schemafile = open(os.path.realpath(TEST_ROOT + '/../schemas/%s.avsc' % name), 'r')
    schema_def = schema.parse(schemafile.read())
    schemafile.close()
    schemafile = None
    return schema_def

if __name__ == "__main__":
    DSSiteSchema = get_schema('site')
    #print(type(DSSiteSchema))
    """
    for field in DSSiteSchema.fields:
        print field
        if type(field.type) == avro.schema.UnionSchema:
            print field.type.schemas[0]
        else:
            print("Not unions schema")
            print field.type
        #print(type(field.type))
    """
    
    DSSITE = {
        "name":'locifood',
        "email":"anemail@demisauce.org",
        "id":12345,
        "slug":"locifood",
        "foreign_id":1
    }
    DSSITE = {
        "name": "TESTING app", 
        "key": "x7456asdfasdf",
        "email": "test@demisauce.org", 
        "enabled":True,
        "id":12345,
        "slug": "unittesting",
        "base_url": "http://testing.demisauce.com",
        "foreign_id":1
    }
    DSSITE = {
        "name": "TESTING app", 
        "key": "x7456asdfasdf", 
        "email": "test@demisauce.org", 
        "slug": "unittesting",
        "base_url": "http://testing.demisauce.com",
        "enabled":True,
        "this_is_extra":"this should go in extra json",
        "this_isa_list":['email2@demisauce.org','email3@demisauce.org']
    }
    site = AvroSchemaSerializer(DSSiteSchema)
    avrosite = site.to_format(DSSITE)
    print("Avro Data = %s" % avrosite)
    result = site.from_avro(avrosite)
    #print dir(DSSiteSchema)
    #print dir(result)
    #print type(result)
    print "DATUM = %s" % (str(result))
    print result['name'] == DSSITE['name']

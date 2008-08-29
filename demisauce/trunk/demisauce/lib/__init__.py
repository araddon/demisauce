import re
import datetime
import simplejson
import logging

log = logging.getLogger(__name__)

def slugify(name):
    """
    Convert's a string to a slugi-ifyed string
    
    >>> lib.slugify("aaron's good&*^ 89 stuff")
    'aarons-good-stuff'
    """
    name = re.sub('( {1,100})','-',name)
    name = re.sub('[^a-z\-]','',name)
    name = re.sub('(-{2,50})','-',name)
    return name

def from_json_convert(cls,json):
    """Converts from a json string back to a populated object::
    
        filter = Filter.from_json(json_string)
    """
    pydict = simplejson.loads(json)
    cls_def = pydict['class']
    module = __import__(cls_def[:cls_def.rfind('.')], globals(), 
        locals(), [cls_def[cls_def.rfind('.')+1:]], -1)
    cls = getattr(module, cls_def[cls_def.rfind('.')+1:])
    
    def get_class(attrs):
        classobj = cls()
        
        for key in attrs:
            if key.find('datetime_') == 0:
                attr = key[:]
                setattr(classobj,key[9:],datetime.datetime.fromtimestamp(attrs[key]))
            else:
                log.debug('from_json setting %s = %s' % (key,attrs[key]))
                setattr(classobj,key,attrs[key])
        return classobj
    
    return [get_class(attrs) for attrs in pydict['data']]

def to_json_convert(obj,indents=2):
    """converts to json string, converting non serializeable fields
    to some other format or ignoring them"""
    # cs = time.mktime(self.created.timetuple()) # convert to seconds
    # to get back:  datetime.datetime.fromtimestamp(cs)
    dout = {}
    
    props = [prop for prop in dir(obj) if not callable(getattr(obj, prop)) and prop.find('__')]
    for key in props:
        if type(getattr(obj,key)) == datetime.datetime:
            dout.update({'datetime_%s' % key:time.mktime(getattr(obj,key).timetuple())})
        else:
            print 'key=%s, attr=%s' % (key,getattr(obj,key))
            dout.update({key:getattr(obj,key)})
    cls = str(obj.__class__)
    cls = cls[cls.find('\'')+1:cls.rfind('\'')]
    cls_out = {'class':cls,'data':[dout]}
    return simplejson.dumps(cls_out,sort_keys=True,indent=indents)

class JsonSerializeable(object):
    @classmethod
    def from_json(cls,json):
        """Converts from a json string back to a populated object::
        
            filter = Filter.from_json(json_string)
        """
        return from_json_convert(cls,json)
    
    def to_json(self,indents=2):
        """converts to json string, converting non serializeable fields
        to some other format or ignoring them"""
        return to_json_convert(self,indents)
    

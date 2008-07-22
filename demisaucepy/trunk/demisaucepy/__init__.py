"""
The core Python API for connecting to Demisauce, use as direct library for
connecting to Demisauce web services.
"""
import urllib, urllib2, os, sys, logging
import ConfigParser
import string
import openanything
import datetime
from xmlnode import XMLNode
from demisaucepy import cfg

log = logging.getLogger(__name__)

def LoadConfig(file, config={}):
    """
    returns a dictionary with key's of the ini file
    """
    conf_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_file = os.path.join(conf_dir, file)
    config = config.copy()
    cp = ConfigParser.ConfigParser()
    cp.read(ini_file)
    for sec in cp.sections():
        name = string.lower(sec)
        for opt in cp.options(sec):
            config[string.lower(opt)] = string.strip(cp.get(sec, opt))
    return config

def hash_email(email):
    import hashlib
    return hashlib.md5(email.lower()).hexdigest()

class Dsws(object):
    """
    Container class for return from web service calls
    """
    def __init__(self, method,resource_id,format, **kwargs):
        self.success = False
        self.method = method
        self.format = format
        self.rid = resource_id
        self.api_key = cfg.CFG['demisauce.apikey']
        self.demisauce_url = cfg.CFG['demisauce.url']
        self.url = '%s/api/%s/%s/%s?apikey=%s' % (cfg.CFG['demisauce.url'],format,
                        method,resource_id, cfg.CFG['demisauce.apikey'])
        self.data = None
        self.__xmlnode__ = None
    
    def getxmlnode(self):
        if self.__xmlnode__ == None:
            # probably need to verify we can parse this?
            self.__xmlnode__ = XMLNode(self.data)
        return self.__xmlnode__
    
    xml_node = property(getxmlnode)

class api_object(object):
    """
    Base class for a returned Demisauce object
    """
    def __repr__(self):
        return self.__str__();
    

class Person(api_object):
    """
    The Person class
    """
    @classmethod
    def create_random_email(cls,domain='@demisauce.org'):
        """
        create a random email for testing
        accepts a @demisauce.org domain argument optionally
        """
        import sha, random, hashlib
        return '%s%s' % (sha.new(str(random.random())).hexdigest(),
            domain)
    
    @classmethod
    def by_email(cls,email=''):
        """
        Returns the single person record for this entry
        """
        e = hash_email(email)
        dsitem = demisauce_ws('person',e,format='xml')
        if dsitem.success == True:
            return dsitem.xml_node.person
        else:
            return None
    
    @classmethod
    def all(cls):
        """
        Returns all person entries for your site
        """
        dsitem = demisauce_ws('person',None,format='xml')
        if dsitem.success == True:
            return dsitem.xml_node.person
        else:
            return None
    
    @classmethod
    def by_hashed_email(cls,hemail=''):
        """
        Returns the single person record for this entry
        """
        dsitem = demisauce_ws('person',hemail,format='xml')
        if dsitem.success == True:
            return dsitem.xml_node.person
        else:
            return None
    

class Comment(api_object):
    """
    The Comment class
    """
    @classmethod
    def by_name(cls,name=''):
        """
        Returns the comments record's
        """
        name = urllib.quote_plus(name)
        dsitem = demisauce_ws('comment',name,format='xml')
        if dsitem.success == True:
            poll = dsitem.xml_node.comment
            poll._xml = dsitem.data
            return poll
        else:
            print dsitem.data
            return None


class Poll(api_object):
    """
    The Poll class
    """
    @classmethod
    def by_name(cls,name=''):
        """
        Returns the single poll record for this named poll
        """
        name = urllib.quote_plus(name)
        dsitem = demisauce_ws('poll',name,format='xml')
        if dsitem.success == True:
            poll = dsitem.xml_node.poll
            poll._xml = dsitem.data
            return poll
        else:
            print dsitem.data
            return None
    
    @classmethod
    def all(cls):
        """
        Returns all poll entries for your site
        """
        dsitem = demisauce_ws('poll',None,format='xml')
        if dsitem.success == True:
            return dsitem.xml_node.poll
        else:
            return None
    
    @classmethod
    def by_hashed_email(cls,hemail=''):
        """
        Returns the single person record for this entry
        """
        dsitem = demisauce_ws('person',hemail,format='xml')
        if dsitem.success == True:
            return dsitem.xml_node.person
        else:
            return None
    


def demisauce_ws_get(method,resource_id,data={},cfgl={},format='html'):
    return demisauce_ws(method,resource_id,verb='get',data=data,cfgl=cfgl,format=format)

def demisauce_ws(method,resource_id,verb='get',data={},cfgl={},format='html'):
    """
    Core web service get
    api/format/method/rid?queryparams
    
    examples:
        - api/html/cms/about/demisauce?apikey=myapikey
        - api/xml/email/welcomemessage?apikey=myapikey
        - api/xml/cms/about/demisauce?apikey=myapikey
        - api/json/cms/about/demisauce?apikey=myapikey
    
    Restful operations (create/read/update/delete)
        - api/xml/person/uniqueid?apikey=myapikey  
                (post=add/update, get=read, delete=delete)
    returns
    """
    item = Dsws(method,resource_id,format)
    useragent = 'DemisaucePY/1.0'
    try: 
        log.debug('url = %s' % item.url)
        item.params = openanything.fetch(item.url, data=data,agent=useragent)
        #print item.params['data']
        if item.params['status'] == 500:
            item.message = 'there was an error on the demisauce server, \
                    no content was returned'
            log.error('500 = %s' % item.url)
            return item
        elif item.params['status'] == 404:
            item.message = 'not found'
            log.debug('404 = %s' % item.url)
            return item
        elif item.params['status'] == 401:
            item.message = 'Invalid API Key'
            log.debug('401 = %s' % item.url)
            return item
        else:
            item.data = item.params['data']
            item.success = True
            item.message = 'success'
            return item
    except urllib2.URLError, err:
        if err[0][0] == 10061:
            log.debug('No Server = %s' % item.url)
            # connection refused
            item.message = 'the remote server didn\'t respond at \
                    <a href=\"%s\">%s</a> ' % (item.url,item.url)
    
    return item

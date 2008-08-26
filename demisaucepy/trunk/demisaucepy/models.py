import urllib, urllib2, os, sys, logging
import ConfigParser
import string
import openanything
import datetime
from xmlnode import XMLNode
from demisaucepy import cfg
from demisaucepy import ServiceDefinition, ServiceClient, \
    ServiceResponse

log = logging.getLogger(__name__)

class RemoteService(object):
    """
    Base class for a returned Demisauce service
    comments = has_many(name='comment',lazy=True,local_key='id' )
    phphello = has_a(name='helloworld',app='phpdemo',lazy=True,local_key='id' )
    """
    def __init__(self,name):
        pass
    
    def from_xml_node(self,node):
        # allow creation from xml node
        pass
    
    def __repr__(self):
        return self.__str__();
    
class Comment(RemoteService):
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



class Person(RemoteService):
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
    

class Comment(RemoteService):
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
    

class Poll(RemoteService):
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
    


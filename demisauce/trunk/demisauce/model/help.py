from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.sql import and_, select
from sqlalchemy.types import Integer, String as DBString, DateTime, \
    Boolean, Text as DBText
from demisauce.model import ModelBase, meta
from demisauce.model import site
from demisauce.model.person import Person
from demisauce.model.tag import Tag
from demisauce.lib.filter import Filter
from demisaucepy.declarative import Aggregagtor, has_a, \
    has_many, aggregator_callable, AggregateView
    
import logging
import formencode
from formencode import validators
from datetime import datetime

helpstatus = {0:'new',1:'assigned',10:'completed'}
helpstatus_map = {'new':0,'assigned':1,'completed':10}

# DB Table:  help/feedback/support ---------------------------
help_table = Table("help", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id'), nullable=False),
        Column('tag_id', None, ForeignKey('tag_map.id')),
        Column("status", Integer, default=0),
        Column("created", DateTime,default=datetime.now()),
        Column("isuser", Boolean, default=False),
        Column("person_id", Integer, nullable=True),
        Column("ip", DBString(24), nullable=True),
        Column("hashedemail", DBString(32), nullable=True),
        Column("email", DBString(150), nullable=True),
        Column("url", DBString(255), nullable=False),
        Column("blog", DBString(255), nullable=True),
        Column("authorname", DBString(100), nullable=True),
        Column("rating_ct", Integer, default=0),
        Column("content", DBText),
    )

# DB Table:  help response ---------------------------
help_response_table = Table("helpresponse", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("help_id", Integer, ForeignKey('help.id')),
        Column("person_id", Integer, ForeignKey('person.id')),
        Column("status", Integer, default=1),
        Column("publish", Boolean, default=0),
        Column("created", DateTime,default=datetime.now()),
        Column("url", DBString(255), nullable=True),
        Column("title", DBString(255), nullable=True),
        Column("rating_ct", Integer, default=0),
        Column("response", DBText),
    )

ModelBaseAggregator = aggregator_callable(ModelBase)



class Help(ModelBaseAggregator):
    """
    Help is the Support/Help/Feedback form
    """
    comments = has_many('comment',lazy=True,local_key='id')
    
    def __init__(self, **kwargs):
        ModelBase.__init__(self,**kwargs)
        if 'email' in kwargs:
            self.set_email(kwargs['email'])
        self.all_tags = None
    
    def set_email(self,email):
        import hashlib
        self.email = email.lower()
        self.hashedemail = hashlib.md5(email.lower()).hexdigest()
    
    def set_user_info(self,user):
        """
        If feedback/help is a user (not anonymous) then
        get much of the info from user object
        """
        if user:
            self.set_email(user.email)
            self.isuser = True
            self.person_id = user.id
            self.blog = user.url
            self.authorname = user.displayname
    
    def get_content(self):
        '''clean up the content'''
        return self.content.replace('\n','<br />').replace('\r','').replace('\\','')
    
    clean_content = property(get_content)
    
    def get_user(self):
        '''grabs person record for submitter'''
        if self.person_id and self.person_id > 0:
            if not hasattr(self,'_person'):
                temp = Person.get(-1,self.person_id)
                if temp:
                    self._person = temp
                else:
                    self._person = None
        return self._person
    
    person = property(get_user)
    
    def get_tags(self):
        '''comma delimted list of tags'''
        return ','.join([tag.value for tag in self.tags])
    
    def set_tags(self, tags, person=None):
        if tags:
            curtags = [tag.value for tag in self.tags]
            tagstemp = [tag.strip() for tag in tags.split(',')]
            tagsnew = [tag for tag in tagstemp if not tag in curtags]
            tagsdelete = [tag for tag in curtags if not tag in tagstemp]
            for tag in tagsnew:
                self.tags.append(Tag(tag=tag,person=person))
            for tag in self.tags:
                if tag.value in tagsdelete:
                    self.tags.remove(tag)
                
    
    tagswcommas = property(get_tags,set_tags)
    
    def get_status_text(self):
        return helpstatus[self.status]
    status_text = property(get_status_text)
    
    def get_others(self):
        '''grabs previous from this user'''
        if self.person_id and self.person_id > 0:
            if not hasattr(self,'_others_from_this_user'):
                temp = meta.DBSession.query(Help).filter_by(person_id=self.person_id
                    ).order_by(help_table.c.created.desc()).limit(10)
                
                if temp:
                    self._others_from_this_user = temp
                else:
                    self._others_from_this_user = []
        return self._others_from_this_user
    others = property(get_others)
    
    @classmethod
    def apply_filter(cls,site_id=0,filter={}):
        qry = meta.DBSession.query(Help).filter_by(site_id=site_id)
        qry = qry
    
    #@classmethod
    #def status_filter(cls,site_id=0,status='new'):
    #    return StatusFilter(site_id=site_id)
    
    @classmethod
    def by_site(cls,site_id=0,ct=15,filter='new',offset=0):
        """Class method to get recent new unprocessed items"""
        return meta.DBSession.query(Help).filter_by(
            site_id=site_id,status=helpstatus_map[filter]
            ).order_by(help_table.c.created.desc()).limit(ct).offset(offset)
    
    @classmethod
    def tag_keys(cls,site_id=0):
        return Tag.by_key(site_id,'help')
    
    @classmethod
    def new_tickets_ct(cls,site_id=0,filter=None):
        """Class method to get count of how many new query tickets 
        there are"""
        return meta.DBSession.query(Help).filter_by(status=helpstatus_map['new'],site_id=site_id).count()
    
    @classmethod
    def recent(cls,site_id=0,ct=15,filter='recent'):
        """Class method to get recent feedbabck items"""
        return meta.DBSession.query(Help).filter_by(site_id=site_id
            ).order_by(help_table.c.created.desc()).limit(ct)
    
    @classmethod
    def for_url(cls,site,url):
        """Class method to get recent help tickets
        for a specific site and url"""
        return meta.DBSession.query(Help).filter_by(site_id=site.id,
            uri=str(url).lower()).all()
    

class HelpResponse(ModelBase,object):
    """
    Response from an admin to feedback entry
    """
    def __init__(self,**kwargs):
        super(HelpResponse, self).__init__(**kwargs)
    
    @classmethod
    def by_site(cls,site_id=0,ct=15,filter='new'):
        """Class method to get recent responded items"""
        return meta.DBSession.query(HelpResponse).filter_by(site_id=site_id
            ).order_by(help__response_table.c.created.desc()).limit(ct)
    
    @classmethod
    def for_url(cls,site,url,ct=5):
        """Class method to get recent help tickets response
        for a specific site and url"""
        return meta.DBSession.query(HelpResponse).filter_by(site_id=site.id,
            url=str(url).lower()).limit(ct)
    


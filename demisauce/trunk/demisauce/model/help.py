from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.sql import and_
from sqlalchemy.types import Integer, String as DBString, DateTime, \
    Boolean, Text as DBText
#from sqlalchemy.types import 
from demisauce.model import ModelBase, meta
from demisauce.model import site

import logging
import formencode
from formencode import validators
from datetime import datetime

helpstatus = {'new':0,'assigned':1,'completed':10}

# DB Table:  help/feedback/support ---------------------------
help_table = Table("help", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("status", Integer, default=0),
        Column("created", DateTime),
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
        Column("created", DateTime),
        Column("url", DBString(255), nullable=True),
        Column("title", DBString(255), nullable=True),
        Column("rating_ct", Integer, default=0),
        Column("response", DBText),
    )

class Help(object,ModelBase):
    """
    Help is the Support/Help/Feedback form
    """
    def __init__(self, site_id=1,email=None,isuser=False):
        self.site_id = site_id
        if email:
            self.set_email(email)
        self.created = datetime.now()
        #,default=datetime.now()
    
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
    
    @classmethod
    def by_site(cls,site_id=0,ct=15,filter='new'):
        """Class method to get recent new unprocessed items"""
        return meta.DBSession.query(Help).filter_by(
            site_id=site_id,status=helpstatus[filter]
            ).order_by(help_table.c.created.desc()).limit(ct)
    
    @classmethod
    def new_tickets_ct(cls,site_id):
        """Class method to get count of how many new query tickets 
        there are"""
        return meta.DBSession.query(Help).filter_by(status=helpstatus['new'],site_id=site_id).count()
    
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
    

class HelpResponse(object,ModelBase):
    """
    Response from an admin to feedback entry
    """
    def __init__(self, help_id,user):
        self.help_id = help_id
        self.site = user.site
        self.person = user
        from datetime import datetime
        self.created = datetime.today()
    
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
    


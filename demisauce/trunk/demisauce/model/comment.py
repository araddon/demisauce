from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.sql import and_
from sqlalchemy.types import Integer, String as DBString, DateTime, \
    Boolean, Text as DBText
#from sqlalchemy.types import 
from demisauce.model import ModelBase, meta
from demisauce.model import site
from demisauce import model

from datetime import datetime
import logging
import formencode
from formencode import validators


# DB Table:  comment ---------------------------
comment_table = Table("comment", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("person_id", Integer, nullable=True),
        Column("created", DateTime,default=datetime.now()),
        Column("isuser", Boolean, default=False),
        Column("hashedemail", DBString(32), nullable=True),
        Column("email", DBString(150), nullable=True),
        Column("type", DBString(50), nullable=False),
        Column("uri", DBString(255), nullable=False),
        Column("blog", DBString(255), nullable=True),
        Column("ip", DBString(24), nullable=True),
        Column("authorname", DBString(100), nullable=True),
        Column("comment", DBText),
    )

class Comment(object,ModelBase):
    """
    Comment is a comment someone makes (may be anonymous) 
    about something. the "Something" is the type, so type=blog or
    type=url (del.icio.us type post), or type=page, etc
    uri is the foreign key, would be "blog_id" if using normal db design
    person is the 32 character md5 hash of the user's email address
    """
    def __init__(self, site_id=1,commenttype="none",isuser=False):
        self.type = commenttype
        self.site_id = site_id
    
    def set_email(self,email):
        import hashlib
        self.email = email.lower()
        self.hashedemail = hashlib.md5(email.lower()).hexdigest()
    
    def set_user_info(self,user):
        """
        If commentor is a user (not anonymous) then
        get much of the info from user object
        """
        if user:
            self.set_email(user.email)
            self.isuser = True
            self.blog = user.url
            self.authorname = user.displayname
    
    def get_comment(self):
        '''clean up the comment'''
        return self.comment.replace('\n','<br />').replace('\r','').replace('\\','')
    clean_comment = property(get_comment)
    
    @classmethod
    def by_site(cls,site_id=0,ct=15):
        """Class method to get recent comments"""
        return meta.DBSession.query(Comment).filter_by(site_id=site_id
            ).order_by(comment_table.c.created.desc()).limit(ct)
    
    @classmethod
    def for_url(cls,site,url):
        """Class method to get recent comments
        for a specific site and url"""
        return meta.DBSession.query(Comment).filter_by(site_id=site.id,
            uri=str(url).lower()).all()
        
    

        
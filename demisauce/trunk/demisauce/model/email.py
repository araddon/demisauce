"""
This is the DataModel to persist to the DB through Sql Alchemy
"""
#!/usr/bin/env python
from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.types import Integer, String as DBString
from sqlalchemy.types import Text as DBText, DateTime
from demisauce import model
from demisauce.model import meta, ModelBase, site

from datetime import datetime

# Define a table.
emailitem_table = Table("email", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("key", DBString(150), nullable=False),
        Column("subject", DBString(120), nullable=False),
        Column("from_email", DBString(150), nullable=False),
        Column("reply_to", DBString(150), nullable=True),
        Column("from_name", DBString(120), nullable=True),
        Column("to", DBString(1000), nullable=True),
        Column("template", DBText, default=''),
        Column("created", DateTime,default=datetime.now()),
    )

class Email(object,ModelBase):
    def __init__(self,site_id, subject, from_email=None, to=None, template=None):
        self.to = to
        self.subject = subject
        self.template = template
        self.key = self.makekey(subject)
        self.site = meta.DBSession.query(model.site.Site).get(site_id)
        self.from_email = self.site.email
    
    def __str__(self):
        return 'email subject=%s key = %s' % (self.subject,self.key)
    
    @classmethod
    def by_key(cls,site_id=0,key=''):
        """
        Gets the template by key for a site::
            
            Email.by_key(c.site_id,'welcome_to_demisauce')
        """
        return meta.DBSession.query(Email).filter_by(site_id=site_id,key=key).first()
    


def get_by_subject(subject):
    """
    Gets a set of content by subject
    """
    return meta.DBSession.query(Email).filter_by(subject=subject).first()

import logging
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.types import Integer, String as DBString
from sqlalchemy.types import Text as DBText, DateTime
from demisauce import model
from demisauce.model import meta, ModelBase, site, JsonMixin
#from demisaucepy.declarative import Aggregator
from datetime import datetime

log = logging.getLogger(__name__)

email_table = Table("email", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("slug", DBString(150), nullable=False),
        Column("subject", DBString(120), nullable=False),
        Column("from_email", DBString(150), nullable=False),
        Column("reply_to", DBString(150), nullable=True),
        Column("from_name", DBString(120), nullable=True),
        Column("to", DBString(1000), nullable=True),
        Column("template", DBText, default=''),
        Column("created", DateTime,default=datetime.now),
)

class Email(ModelBase,JsonMixin):
    schema = email_table
    _allowed_api_keys = ['slug','subject','from_email','reply_to','from_name','to','template']
    def __init__(self, **kwargs):
        super(Email, self).__init__(**kwargs)
    
    def after_load(self):
        if ((not hasattr(self,'slug')) or self.slug == None) and self.subject != None:
            self.slug = self.makekey(self.subject)
        if hasattr(self,'site_id') and not hasattr(self,'from_email'):
            self.site = meta.DBSession.query(model.site.Site).get(self.site_id)
            self.from_email = self.site.email
    
    def __str__(self):
        return 'site_id=%s, email subject=%s slug = %s' % (self.site_id, self.subject,self.slug)
    
    @classmethod
    def all(cls,site_id=0):
        """
        Gets all for this site::
        
            Email.all(site_id=c.site_id)
        """
        return meta.DBSession.query(Email).filter_by(site_id=site_id)
    
    @classmethod
    def by_slug(cls,site_id=0,slug=''):
        """
        Gets the template by slug for a site::
            
            Email.by_slug(c.site_id,'welcome_to_demisauce')
        """
        qry = meta.DBSession.query(Email).filter_by(site_id=site_id,slug=slug)
        #log.debug(qry)
        return qry.first()
    

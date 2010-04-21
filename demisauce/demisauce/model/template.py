import logging
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.types import Integer, String as DBString
from sqlalchemy.types import Text as DBText, DateTime
from demisauce import model
from demisauce.model import meta, ModelBase, site, SerializationMixin
#from demisaucepy.declarative import Aggregator
from datetime import datetime

log = logging.getLogger('demisauce')

template_table = Table("template", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("slug", DBString(150), nullable=False),
        Column("subject", DBString(120), nullable=False),
        Column("from_email", DBString(150), nullable=False),
        Column("reply_to", DBString(150), nullable=True),
        Column("from_name", DBString(120), nullable=True),
        Column("to", DBString(1000), nullable=True),
        Column("template", DBText, default=''),
        Column("template_html", DBText, default=''),
        Column("created", DateTime,default=datetime.now),
        Column("extra_json", DBText, default=''),
)

class Template(ModelBase,SerializationMixin):
    schema = template_table
    _allowed_api_keys = ['slug','subject','from_email','reply_to','from_name','to','template']
    def __init__(self, **kwargs):
        super(Template, self).__init__(**kwargs)
    
    def save(self):
        if self.slug == None and self.subject != None:
            self.slug = model.slugify(self.subject)
        super(Template, self).save()
    
    def after_load(self):
        if hasattr(self,'site_id') and not hasattr(self,'from_email'):
            self.site = meta.DBSession.query(model.site.Site).get(self.site_id)
            self.from_email = self.site.email
    
    def __str__(self):
        return 'site_id=%s, email subject=%s slug = %s' % (self.site_id, self.subject,self.slug)
    
    @classmethod
    def all(cls,site_id=0):
        """
        Gets all for this site::
        
            Template.all(site_id=c.site_id)
        """
        return meta.DBSession.query(Template).filter_by(site_id=site_id)
    
    @classmethod
    def by_slug(cls,site_id=0,slug=''):
        """
        Gets the template by slug for a site::
            
            Template.by_slug(c.site_id,'welcome_to_demisauce')
        """
        qry = meta.DBSession.query(Template).filter_by(site_id=site_id,slug=slug)
        #log.debug(qry)
        return qry.first()
    

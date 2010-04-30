from sqlalchemy import Column, MetaData, Table
from sqlalchemy.types import Integer, String as DBString, DateTime, \
    Text as DBText, Boolean
from sqlalchemy.sql import func
from demisauce import model
from demisauce import lib 
#from demisauce.model import mapping
from demisauce.model import SerializationMixin
from demisauce.model import meta, ModelBase
from demisauce.model.config import ConfigMixin, ConfigAttribute
from datetime import datetime
import re, hashlib, random, json, logging

log = logging.getLogger('demisauce.model')

site_table = Table("site", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("email", DBString(255)),
        Column("name", DBString(255)),
        Column("slug", DBString(50)),
        Column("sharedsecret", DBString(50)),
        Column("description", DBText),
        Column("key", DBString(50)),
        Column("base_url", DBString(255),nullable=False,default='http://localhost:4950'),
        Column("site_url", DBString(255),nullable=False,default='http://yoursite.com/'),
        Column("created", DateTime,default=datetime.now),
        Column("last_update", DateTime,default=datetime.now),
        Column("extra_json", DBText),
        Column("send_invites", Boolean, default=False),
        Column("enabled", Boolean, default=False),
        Column("public", Boolean, default=False),
        Column("is_sysadmin", Boolean, default=False),
    )

class Site(ModelBase,SerializationMixin,ConfigMixin):
    """
    Container for different user's and distinct sets of data.  Each Site 
    does not share anything with other site's.  Users in a site can be in 
    groups together etc.
    
    :slug: short string identifier of site, for use
            in querystring's and urls's such as
            http://yourslug.demisauce.com
    :key:  private key to be used by api connection to site
    :base_url:  base url of site (http://localhost:4950 if dev etc)
    :site_url:  base url of site you use demisauce on
    :enabled:  has this site been configured to allow usage?
    :settings: configuration settings
    """
    schema = site_table
    _readonly_keys = ['id','key','created','last_update','enabled','public','is_sysadmin','apps','datetime_created']
    _allowed_api_keys = ['email','name','slug','description','base_url','site_url','extra_json']
    def __init__(self, **kwargs):
        self.slug = None
        super(Site, self).__init__(**kwargs)
        self.key = Site.create_sitekey()
        self.sharedsecret = Site.create_sitekey()
        if self.slug == None and hasattr(self,'name') and self.name != None:
            self.slug = lib.slugify(self.name.lower())
    
    # =====  Serialization
    def to_json(self,keys=None):
        output = self.to_dict(keys=keys)
        if hasattr(self,'settings'):
            attributes = []
            for attr in self.settings:
                attributes.append(attr.to_dict())
            output['settings'] = attributes
        return json.dumps(output)
    
    def from_json(self,json_string):
        """
        Chainable - Converts from a json string back to a populated object::
            
            site = Site().from_json(json_string)
        
        """
        json_dict = json.loads(json_string)
        self.from_dict(json_dict)
        if 'settings' in json_dict:
            for attribute in json_dict['settings']:
                self.settings.append(ConfigAttribute().from_dict(attribute))
        
        return self
    
    
    def delete(self):
        for att in self.settings:
            att.delete()
        super(Site, self).delete()
    
    @classmethod
    def create_sitekey(cls):
        return hashlib.md5(str(random.random())).hexdigest()
    
    def __str__(self):
        return '''{id:%s,name:'%s',slug:'%s',base_url:'%s'}''' % (self.id,
                self.name, self.slug, self.base_url)
    
    @classmethod
    def by_slug(cls,slug):
        """get site by slug"""
        return meta.DBSession.query(Site).filter_by(slug=slug).first()
    
    @classmethod
    def by_apikey(cls,apikey):
        """get site by apikey"""
        return meta.DBSession.query(Site).filter_by(key=apikey).first()
    

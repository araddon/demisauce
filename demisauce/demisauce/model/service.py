"""
A service registry application base.  
"""
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.types import Integer, String as DBString, DateTime, \
    Text as DBText, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import eagerload

from demisauce import model
from demisauce.model import meta, ModelBase, JsonMixin
from demisauce.model.site import Site
from datetime import datetime

app_table = Table("app", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("owner_id", Integer, ForeignKey('person.id')),
        Column("created", DateTime,default=datetime.now),
        Column("list_public", Boolean, default=False),
        Column("name", DBString(50)),
        Column("slug", DBString(50)),
        Column("base_url", DBString(255)),
        Column("url_format", DBString(255),nullable=True),
        Column("authn", DBString(50),default='None'),
        Column("description", DBText),
    )

class App(ModelBase,JsonMixin):
    """
    Application is collection of services, or pre-done integration
    usually apps share authentication, base_url etc.
    info about service, partly from declatative (in code)
    partly from app registration/webadmin, partly config ???
    
    :name: name of the Application
    :slug: url/app friendly key for this app
    :description:  description of Application
    :base_url:  base url of site (http://localhost:4950 if dev etc)
    :site:  site of this app
    :authn:  which authN method?
    :list_public:  True/False to show publicly for other users and accounts
    """
    schema = app_table
    def __init__(self, **kwargs):
        super(App, self).__init__(**kwargs)
    
    @classmethod
    def by_site(cls,site_id):
        """get list of apps by site::
        
            App.by_site(c.site_id)
        """
        return meta.DBSession.query(App).filter_by(site_id=site_id).all()
    

service_table = Table("service", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("app_id", Integer, ForeignKey('app.id')),
        Column("owner_id", Integer, ForeignKey('person.id')),
        Column("created", DateTime,default=datetime.now),
        Column("last_update",DateTime,default=datetime.now,onupdate=datetime.now),
        Column("cache_time", Integer, default=900),
        Column("list_public", Boolean, default=False),
        Column("format", DBString(30),default='json'),
        Column("name", DBString(255)),
        Column("method_url", DBString(255)),
        Column("key", DBString(255)),
        Column("views", DBString(255)),
        Column("description", DBText),
    )

class Service(ModelBase,JsonMixin):
    """
    Service is either a Demisauce, or "plug_in" service
    many->many:  a "plugin" like wordpress could have many 
    implementations but behave the same
    
    :app: What application is this member of
    :name: name of the service
    :key:  url friendly version of name
    :description:  description of service
    :method_url:  /comment/commentform - combined with base
        app url will allow enough destination info
    :cache_time:   cache time
    :authz:  public, admin, logged on, ?  role based(??)
    :params:  which parameters need to get passed and how, format?
    :views: [list]{format: json/xml/googlegadget/html}
    :events: [list]{format: xmpp, callback, email, plugin?}
    :dependency: ??  list of dependencies  (js? css? kinda like "requires?")
    """
    @property
    def url(self):
        if self.app and self.app.base_url:
            return "%s%s" % (self.app.base_url,self.method_url)
        if self.site:
            return "%s%s" % (self.site.base_url,self.method_url)
    
    schema = service_table
    @classmethod
    def all(cls):
        """Class method to get recent help tickets
        for a specific site and url"""
        return meta.DBSession.query(Service).options(eagerload('site')).options(eagerload('app'))
    
    @classmethod
    def by_app_service(cls,servicekey=''):
        """Class method to get """
        #return meta.DBSession.query(Service).filter_by(key=str(key).lower()).options(eagerload('site'))
        return meta.DBSession.query(Service).filter_by(key=str(servicekey).lower()).first()
    
    @classmethod
    def recent_updates(cls,ct=10):
        """Class method to get all recently updated public services"""
        #return meta.DBSession.query(Service).filter_by(key=str(key).lower()).options(eagerload('site'))
        return meta.DBSession.query(Service).filter_by(list_public=True
            ).order_by(Service.last_update.desc()).limit(ct)
    

"""
A service registry application base.  
"""
from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.types import Integer, String as DBString, DateTime, \
    Text as DBText, Boolean
from sqlalchemy.sql import func
from demisauce import model
from demisauce.model import meta, ModelBase
from datetime import datetime

app_table = Table("app", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("owner_id", Integer, ForeignKey('person.id')),
        Column("created", DateTime,default=datetime.now()),
        Column("name", DBString(255)),
        Column("base_url", DBString(255)),
        Column("authn", DBString(50)),
        Column("description", DBText),
    )

class App(ModelBase):
    """
    Application is collection of services, or pre-done integration
    usually apps share authentication, base_url etc.
    info about service, partly from declatative (in code)
    partly from app registration/webadmin, partly config ???
    
    :name: name of the service
    :description:  description of service
    :base_url:  base url of site (http://localhost:4950 if dev etc)
    :authn:  which authN method?
    :cache:  where to cache (memcached, config etc)
    :env:   [dev,test,prod] (needed???  or ?:  leave for later)
    """
    
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
        Column("created", DateTime,default=datetime.now()),
        Column("name", DBString(255)),
        Column("url", DBString(255)),
        Column("key", DBString(255)),
        Column("description", DBText),
    )

class Service(ModelBase):
    """
    Service is either a Demisauce, or "plug_in" service
    many->many:  a "plugin" like wordpress could have many 
    implementations but behave the same
    
    :app: What application is this member of
    :name: name of the service
    :description:  description of service
    :relative_url:  /comment/commentform - combined with base
        app url will allow enough destination info
    :cache:   cache time, maybe which cache to use, per person, role?
    :authz:  public, admin, logged on, ?  role based(??)
    :params:  which parameters need to get passed and how, format?
    :views: [list]{format: json/xml/googlegadget/html}
    :events: [list]{format: xmpp, callback, email, plugin?}
    """
    pass
    

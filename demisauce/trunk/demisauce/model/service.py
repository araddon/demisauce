"""
A service registry application base.  
"""
from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.types import Integer, String as DBString, DateTime, \
    Text as DBText, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import eagerload

from demisauce import model
from demisauce.model import meta, ModelBase
from demisauce.model.site import Site
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
        Column("views", DBString(255)),
        Column("description", DBText),
    )

class Service(ModelBase):
    """
    Service is either a Demisauce, or "plug_in" service
    many->many:  a "plugin" like wordpress could have many 
    implementations but behave the same
    
    :app: What application is this member of
    :name: name of the service
    :key:  url friendly version of name
    :description:  description of service
    :relative_url:  /comment/commentform - combined with base
        app url will allow enough destination info
    :cache:   cache time, maybe which cache to use, per person, role?
    :authz:  public, admin, logged on, ?  role based(??)
    :params:  which parameters need to get passed and how, format?
    :views: [list]{format: json/xml/googlegadget/html}
    :events: [list]{format: xmpp, callback, email, plugin?}
    :dependency: ??  list of dependencies  (js? css? kinda like "requires?")
    """
    @classmethod
    def all(cls):
        """Class method to get recent help tickets
        for a specific site and url"""
        return meta.DBSession.query(Service).options(eagerload('site')).options(eagerload('app'))
    
    @classmethod
    def by_key(cls,key=''):
        """Class method to get recent help tickets
        for a specific site and url"""
        return meta.DBSession.query(Service).options(eagerload('site')).filter_by(key=str(key).lower()).first()
        
    def nodelist_wperson_ratings(node,current_userid,site_id,recent=False,count=15):
        """Gets a Node, and determines if current user has rated any of the
            nodes.
        """
        rating_der = select([rating_table],rating_table.c.person_id==current_userid).alias('rating_der')
        #statement = node_table.outerjoin(rating_der,node_table.c.id==rating_der.c.obj_id).select(use_labels=True)
        qry = model.DBSession.query(Node).options(contains_eager("ratings",alias=rating_der))
        if node == None and recent == False:
            order_by_clause = node_table.c.rating_ct.desc()
        elif recent == True:
            order_by_clause = node_table.c.created.desc()
        else:
            order_by_clause = node_table.c.rating_ct.desc()

        qry = qry.from_statement(node_table.outerjoin(
                                rating_der,node_table.c.id==rating_der.c.obj_id
                        ).select(and_(Node.role=='pu',Node.site_id==site_id),use_labels=True
                                ).order_by(order_by_clause)
                )
        #print 'site_id=%s' % (site_id)
        #print qry
        result = qry.all()
        return result, qry
    

"""
"""
import logging, re, time, json, datetime
from tornado import escape
from sqlalchemy import create_engine
from sqlalchemy import Column, MetaData, Table, types
from sqlalchemy import engine, orm
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
from demisauce.model import meta
from tornado.options import define, options
from demisaucepy.serializer import SerializationMixin
import redis
from pythonsolr.pysolr import Solr
from gearman import GearmanClient

log = logging.getLogger(__name__)

def slugify(name):
    """
    Convert's a string to a slugi-ifyed string
    
    >>> slugify("aaron's good&*^ 89 stuff")
    'aarons-good-stuff'
    """
    name = name.lower()
    name = re.sub('( {1,100})','-',name)
    name = re.sub('[^a-z0-9\-]','',name)
    #name = re.sub('(-{2,50})','-',name)
    return name

class sqlalchemydb(object):
    def __init__(self,engine=None,session=None,metadata=None,
        redis_host="localhost",cache=None,gearman_client=None):
        self.engine = engine
        self._session_loaded = False
        self._session = session
        self.metadata = metadata
        self._redis_host = redis_host
        self._cache = cache
        self._gearman_client = gearman_client
    
    def save(self,instance):
        s = self._session()
        s.add(instance)
        s.commit()
    
    def get_session(self):
        if not self._session_loaded:
            self._session()
        return self._session
    
    session = property(get_session)
    def get_redis(self):
        if hasattr(self,"_redis"):
            return self._redis
        else:
            self._redis = redis.Redis(host=self._redis_host,pooled=True)
        return self._redis
    
    redis = property(get_redis)
    def get_cache(self):
        return self._cache
    
    cache = property(get_cache)
    @property
    def gearman_client(self):
        return self._gearman_client
    
    def finish(self):
        """Called to commit and clean up db for this request"""
        #log.debug("sqlalchemydb:  Finish -> session commit ")
        #self._session.commit()
        self._session.close()
        pass
    

def get_database(cache=None):
    """Brokers creation of the SqlAlchemy session
        using settings info, also sets host/ports for redis etc
        Manages session for SA
    """
    gearman_client = GearmanClient(options.gearman_servers)
    #creator=connect,  , 
    #pool_recycle=True # performance was horrible with this
    meta.engine = create_engine(options.sqlalchemy_default_url,
            echo=options.sqlalchemy_default_echo, pool_recycle=3600)
    logging.debug("Setting up db with connection = %s" % options.sqlalchemy_default_url)
    sm = orm.sessionmaker(autoflush=True, bind=meta.engine)
    meta.DBSession = orm.scoped_session(sm)
    db = sqlalchemydb(engine=meta.engine,
        session=meta.DBSession,
        metadata=meta.metadata,
        redis_host=options.redis_host,
        cache=cache,
        gearman_client=gearman_client)
    return db

def init_model(enginelocal):
    """
    Call me before using any of the tables or classes in the model.
    """
    
    sm = orm.sessionmaker(autoflush=True, bind=enginelocal)
    meta.engine = enginelocal
    meta.DBSession = orm.scoped_session(sm)


def setup_site(user):
    """does the base site setup for a new account
    """
    from demisauce.lib import slugify
    app = service.App(site_id=user.site_id,owner_id=user.id)
    app.slug = slugify(user.site.name)
    app.name = user.site.name
    app.base_url = user.site.base_url
    app.save()

def create_schema():
    #metadata.bind = config['pylons.g'].sa_engine
    print 'in create schema'
    meta.metadata.create_all(config['pylons.g'].sa_engine)

def make_key(key):
    """
    Converts a string title to a url safe key that is unique per site
    """
    import urllib
    return urllib.quote_plus(key.lower().replace(' ','_'))

def reverse_key(key):
    """
    Converts a url safe key to the item in the db
    """
    import urllib
    return urllib.quote_plus(key.replace(' ','_'))

class ModelBase(object):
    """
    Abstract base class implementing some shortcuts
    """
    _allowed_api_keys = []
    __all_schema_keys__ = None
    def __init__(self,**kwargs):
        self._is_cache = False
        for key in kwargs:
            if hasattr(self,key):
                setattr(self,key,kwargs[key])
        self.on_new()
    
    @orm.reconstructor
    def init_on_load(self):
        self._is_cache = False
    
    def get_keys(self):
        if hasattr(self.__class__,"__all_schema_keys__"):
            if self.__class__.__all_schema_keys__ == None:
                logging.debug("getting all keys from schema?  %s" % self.__class__)
                self.__class__.__all_schema_keys__ = [c.name for c in self.__class__.schema.c]
            return self.__class__.__all_schema_keys__
        return []
    
    def on_new(self):
        pass
    
    def makekey(self,key):
        """
        Converts a string title to a url safe key that is unique per site
        """
        return make_key(key)
    
    def after_load(self):
        pass
    
    def isvalid(self):
        return True
    
    def delete(self):
        meta.DBSession.delete(self)
        meta.DBSession.commit()
    
    def save_extra(self):
        if hasattr(self,'extra_json') and isinstance(self.extra_json,(list,dict)):
            json_str = json.dumps(self.extra_json)
            self.extra_json = json_str
    
    def save(self):
        self.save_extra()
        meta.DBSession.add(self)
        meta.DBSession.commit()
    
    @classmethod
    def all(cls,site_id=0):
        """Class method to get all
        using the native SqlAlchemy get instead of site_id specific one"""
        if site_id == -1:
            return meta.DBSession.query(cls).all()
        else:
            return meta.DBSession.query(cls).filter_by(site_id=site_id,id=id).all()
    
    @classmethod
    def get(cls,site_id=0,id=0):
        """Class method to get by id
        using the native SqlAlchemy get instead of site_id specific one"""
        #return meta.DBSession.query(cls).get(id)
        if site_id == -1:
            return meta.DBSession.query(cls).get(id)
        else:
            qry = meta.DBSession.query(cls).filter_by(site_id=site_id,id=id)
            #log.debug('in get: %s' % str(qry))
            return qry.first()
    
    @classmethod
    def saget(cls,id=0):
        """Class method to get by id"""
        return meta.DBSession.query(cls).get(id)
    


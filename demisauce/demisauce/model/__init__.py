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

from demisaucepy import cache, cache_setup

log = logging.getLogger('demisauce.model')

CACHE_DURATION = 3600


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
    #cache_setup.load_memcache()
    meta.engine = create_engine(options.sqlalchemy_default_url,
            echo=options.sqlalchemy_default_echo, pool_recycle=3600)
    log.debug("Setting up db with connection = %s" % options.sqlalchemy_default_url)
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
        self.is_new = False
        for key in kwargs:
            #if hasattr(self,key):
            setattr(self,key,kwargs[key])
        self.on_new()
    
    @orm.reconstructor
    def init_on_load(self):
        self.on_new()
        self._is_cache = False
        self.is_new = False
    
    def get_keys(self):
        if hasattr(self.__class__,"__all_schema_keys__"):
            if self.__class__.__all_schema_keys__ == None:
                keys = []
                keys = [c.name for c in self.__class__.schema.c]
                self.__class__.__all_schema_keys__ = keys
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
    
    def save_extra(self):
        if hasattr(self,'extra_json') and isinstance(self.extra_json,(list,dict)):
            json_str = json.dumps(self.extra_json)
            self.extra_json = json_str
    
    def save(self):
        if self.id > 0:
            self.is_new = False
        else:
            self.is_new = True
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
    
    def delete(self):
        try: 
            log.debug("in delete %s" % self.__class__)
            meta.DBSession.delete(self)
            meta.DBSession.commit()
        except:
            meta.DBSession.rollback() #.close()
            logging.error("Error in ModelBase.delete():  %s" % traceback.print_exc())
    
    def delete_cache(self):
        try: 
            log.debug("in delete cache %s" % self.__class__)
            jsons = cache.cache.get(self.__class__.cache_key(self.id))
            if jsons and jsons.find("{") == -1:  # if not json, must be cache key
                cache.cache.delete(self.__class__.cache_key(jsons))
            cache.cache.delete(self.__class__.cache_key(self.id))
        except:
            logging.error("Error in ModelBase.delete_cache():  %s" % traceback.print_exc())
    
    def update_cache(self,jsons=None):
        'Update and save json to mc'
        if not jsons:
            jsons = self.to_json()
        ptr = self.id
        if hasattr(self,'pointer'):
            ptr = self.pointer
            if self.id != ptr:
                cache.cache.set(self.__class__.cache_key(self.id),ptr)
        log.debug("saving key=%s, val=%s" % (self.__class__.cache_key(ptr),'jsons'))
        cache.cache.set(self.__class__.cache_key(ptr),jsons,CACHE_DURATION)
        return jsons
    
    def after_load(self):
        pass
    
    @classmethod
    def cache_key(cls,id):
        'simple cachkey of DS-classname-id '
        cls_name = str(cls)
        cls_name = cls_name[cls_name.rfind('.')+1:cls_name.rfind('\'')].lower()
        return re.sub('(\s)','',str("DS-%s-%s" % (cls_name,id)))
    
    @classmethod 
    def get_manymc(cls,ids):
        cls_name = str(cls)
        cls_name = cls_name[cls_name.rfind('.')+1:cls_name.rfind('\'')].lower()
        keys = [cls.cache_key(id) for id in ids]
        vals = cache.cache.get_many(keys)
        logging.debug("getmanymc = %s, %s" % (keys,'vals'))
        objects = []
        for id in ids:
            key = cls.cache_key(id)
            if vals.has_key(key):
                val = vals[key]
                if val and val.find("{") == -1:
                    v = cache.cache.get(cls.cache_key(val))
                    if not v:
                        o = cls.get(id)
                        if o:
                            v = o.update_cache()
                        else:
                            log.error("no item found for id = %s" % id)
                    #log.debug("id = %s, val=%s, k = %s, v=%s" % (id, val, cls.cache_key(val),v == None))
                    vals[key] = v
            else:
                o = cls.saget(id)
                if o:
                    logging.debug("Updating Cache in %s - %s" % (key,id))
                    jsons = o.update_cache()
                    vals.update({key:jsons})
                else:
                    log.error("wtf?  no o? key = %s id=%s" % (key,id))
        for k,v in vals.iteritems():
            if v in (None,''):
                log.error("missing cache entry for %s" % key)
            obj = cls().from_json(v)
            objects.append(obj)
        return objects
    
    @classmethod
    def get_cache(cls,id=0,reload=False):
        """Class method to get from cache by id"""
        jsons = None
        cache_key = cls.cache_key(id)
        if reload == True:
            o = cls.saget(id)
        else:
            jsons = cache.cache.get(cls.cache_key(id))
            if jsons and jsons.find("{") == -1:  # if not json, must be cache key
                log.debug('jsons find == -1  %s' % jsons)
                try: 
                    cache_key = cls.cache_key(jsons)
                    jsons = cache.cache.get(cache_key)
                except:
                    logging.error("Error in ModelBase.get_cache():  %s" % cache_key)
                
            if not jsons:
                o = cls.saget(id)
        if not jsons and o:
            log.debug('cache not found, updating cache %s' % (cache_key))
            jsons = o.update_cache()
        if jsons:
            o = cls()
            o.from_json(jsons)
            o._is_cache = True
        else:
            logging.error("no jsons? %s" % cache_key)
        return o
    

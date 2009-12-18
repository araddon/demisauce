"""
"""
import logging
from tornado import escape
import time, simplejson, datetime
from sqlalchemy import create_engine
from sqlalchemy import Column, MetaData, Table, types
from sqlalchemy import engine, orm
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
from demisauce.model import meta
from tornado.options import define, options

import redis
from pythonsolr.pysolr import Solr
from gearman import GearmanClient

log = logging.getLogger(__name__)

define("sqlalchemy_default_url", default=("mysql://root:demisauce@192.168.1.7/demisauce"))
define("sqlalchemy_default_echo", default="True")

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
    

def get_database(settings,cache=None):
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


class JsonMixin(object):
    _json_ignore_keys = []
    def to_dict(self,keys=None):
        """serializes to dictionary, converting non serializeable fields
        to some other format or ignoring them"""
        # cs = time.mktime(self.created.timetuple()) # convert to seconds
        # to get back:  datetime.datetime.fromtimestamp(cs)
        dout = {}
        ignore_keys = []
        
        if not keys:
            logging.debug("getting all keys from schema?  %s" % self.__class__)
            keys = [c.name for c in self.__class__.schema.c] 
        
        if hasattr(self.__class__,"_json_ignore_keys"):
            ignore_keys = self.__class__._json_ignore_keys
        
        for key in keys:
            if key not in ignore_keys and key.find("_") != 0 and hasattr(self,key):
                attr = getattr(self,key)
                if type(attr) == datetime or type(attr) == datetime.datetime:
                    dout.update({u'datetime_%s' % key:time.mktime(attr.timetuple())})
                elif type(attr) == str:
                    dout.update({key:attr})
                else:
                    dout.update({key:attr})
        logging.debug(dout)
        return dout
    
    def to_json(self,keys=None):
        return escape.json_encode(self.to_dict(keys=keys))
    
    def from_dict(self,json_dict):
        """
        Chainable - Converts from a json python dictionary
        back to a populated object::
            
            peep = Person().from_dict(json_dict)
        
        """
        
        keys = [c.name for c in self.__class__.schema.c]
        
        _start_time = time.time()
        #logging.debug("from_json after pre Time:  %.2fms", (1000.0 * (time.time() - _start_time)))
        self._json = json_dict # save decoded json
        for key in json_dict:
            if key in keys:
                if key.find('datetime_') == 0:
                    setattr(self,key[9:],datetime.fromtimestamp(float(json_dict[key])))
                else:
                    setattr(self,key,json_dict[key])
        
        #logging.debug("from_json after Time:  %.2fms", (1000.0 * (time.time() - _start_time)))
        return self
    
    def from_json(self,json_string):
        """
        Chainable - Converts from a json string back to a populated object::
            
            peep = Person().from_json(json_string)
        
        """
        self.from_dict(escape.json_decode(json_string))
        return self
    


def test_connect():
    """Used for Nosetests which needs the MetaData to
    be connected to the engine
    """
    meta.metadata.bind = config['pylons.g'].sa_engine
    meta.DBSession = scoped_session(sessionmaker(autoflush=True,
            transactional=True, bind=config['pylons.g'].sa_engine))
    #pass


def setup_site(user):
    """does the base site setup for a new account
    """
    from demisauce.model import cms, email, service
    from demisauce.fixturedata import site_emails
    from demisauce.lib import slugify
    app = service.App(site_id=user.site_id,owner_id=user.id)
    app.slug = slugify(user.site.name)
    app.name = user.site.name
    app.base_url = user.site.base_url
    app.save()
    cmsitem = meta.DBSession.query(cms.Cmsitem).filter_by(site_id=user.site_id,
        item_type='root').first()
    if not cmsitem:
        cmsitem = cms.Cmsitem(user.site_id, 'root','root, do not edit')
        cmsitem.item_type='root'
        cmsitem.save()
    for e in site_emails:
        emailitem = email.Email(site_id=user.site_id,subject=e['subject'])
        emailitem.template = e['template']
        emailitem.from_name = e['from_name']
        emailitem.from_email = e['from_email']
        emailitem.key = emailitem.makekey(emailitem.subject)
        emailitem.save()
    

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
    def __init__(self,**kwargs):
        for key in kwargs:
            if hasattr(self,key):
                setattr(self,key,kwargs[key])
    
    def makekey(self,key):
        """
        Converts a string title to a url safe key that is unique per site
        """
        return make_key(key)
    
    @classmethod
    def XXXfrom_json(cls,json):
        """
        Converts from a json string back to a populated object::
            
            peep = Person.from_json(json_string)
        
        """
        pydict = simplejson.loads(json)
        cls_def = pydict['class']
        module = __import__(cls_def[:cls_def.rfind('.')], globals(), 
            locals(), [cls_def[cls_def.rfind('.')+1:]], -1)
        cls = getattr(module, cls_def[cls_def.rfind('.')+1:])
        
        def get_class(attrs):
            if 'id' in attrs and 'site_id' in attrs:
                classobj = cls.get(attrs['site_id'],attrs['id'])
            else:
                classobj = cls()
            
            for key in attrs:
                if key.find('datetime_') == 0:
                    attr = key[:]
                    setattr(classobj,key[9:],datetime.datetime.fromtimestamp(attrs[key]))
                else:
                    log.debug('from_json setting %s = %s' % (key,attrs[key]))
                    setattr(classobj,key,attrs[key])
            return classobj
        
        return [get_class(attrs) for attrs in pydict['data']]
    
    def XXXto_json(self,indents=2):
        """converts to json string, converting non serializeable fields
        to some other format or ignoring them"""
        # cs = time.mktime(self.created.timetuple()) # convert to seconds
        # to get back:  datetime.datetime.fromtimestamp(cs)
        dout = {}
        
        for key in self.c._data:
            if type(getattr(self,key)) == datetime.datetime:
                dout.update({'datetime_%s' % key:time.mktime(getattr(self,key).timetuple())})
            else:
                dout.update({key:getattr(self,key)})
        cls = str(self.__class__)
        cls = cls[cls.find('\'')+1:cls.rfind('\'')]
        cls_out = {'class':cls,'data':[dout]}
        return simplejson.dumps(cls_out,sort_keys=True,indent=indents)
    
    def delete(self):
        meta.DBSession.delete(self)
        meta.DBSession.commit()
    
    def save(self):
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
            log.debug('in get: %s' % str(qry))
            return qry.first()
    
    @classmethod
    def saget(cls,id=0):
        """Class method to get by id"""
        print("getting cls=%s    id=%s  idtype = %s" %(cls,id,type(id)))
        item = meta.DBSession.query(cls).get(id)
        print("item.id = %s, type = %s" % (item.id,type(item.id)))
        return meta.DBSession.query(cls).get(id)
    

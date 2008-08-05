"""
"""
import logging
from pylons import config
from sqlalchemy import Column, MetaData, Table, types
from sqlalchemy import engine, orm
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
from demisauce.model import meta

def init_model(enginelocal):
    """
    Call me before using any of the tables or classes in the model.
    """
    
    sm = orm.sessionmaker(autoflush=True, transactional=True, bind=enginelocal)
    meta.engine = enginelocal
    meta.DBSession = orm.scoped_session(sm)


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
    from demisauce.model import cms, email
    from demisauce.fixturedata import site_emails
    cmsitem = meta.DBSession.query(cms.Cmsitem).filter_by(site_id=user.site_id,
        item_type='root').first()
    if not cmsitem:
        cmsitem = cms.Cmsitem(user.site_id, 'root','root, do not edit')
        cmsitem.item_type='root'
        cmsitem.save()
    for e in site_emails:
        emailitem = email.Email(user.site_id,e['subject'])
        emailitem.template = e['template']
        emailitem.from_name = e['from_name']
        emailitem.from_email = e['from_email']
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
    
class ModelBase:
    """
    Abstract base class implementing some shortcuts
    """
    __tjsonkeys__ = []
    def __init__(self):
        pass
    
    def makekey(self,key):
        """
        Converts a string title to a url safe key that is unique per site
        """
        return make_key(key)

    def delete(self):
        meta.DBSession.delete(self)
        meta.DBSession.commit()

    def save(self):
        if self.id > 0:
            meta.DBSession.update(self)
        else:
            meta.DBSession.save(self)
        
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
            return meta.DBSession.query(cls).filter_by(site_id=site_id,id=id).first()
    
    @classmethod
    def saget(cls,id=0):
        """Class method to get by id"""
        return meta.DBSession.query(cls).get(id)
    

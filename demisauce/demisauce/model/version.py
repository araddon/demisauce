import logging, json
from sqlalchemy import Column, MetaData, ForeignKey, Table, \
    func, UniqueConstraint
from sqlalchemy import Integer, String as DBString, DateTime, Boolean, \
    Text as DBText
from sqlalchemy import engine, orm
from sqlalchemy.orm import mapper, relation, class_mapper, synonym, dynamic_loader
from sqlalchemy.sql import and_, text
from datetime import datetime
import formencode
import random, hashlib, string
from wtforms import Form, BooleanField, TextField, TextAreaField, \
    PasswordField, SelectField, SelectMultipleField, HiddenField, \
    IntegerField, validators
from wtforms.validators import ValidationError
from tornado import escape
from tornado.options import options
from demisauce import model
from demisauce.model import meta
from demisauce.model import ModelBase, SerializationMixin
from datetime import datetime

log = logging.getLogger("demisauce")


version = Table('version', meta.metadata,
     Column('id', Integer, primary_key=True),
     Column("version", Integer, default = 0),
     Column('person_id', None, ForeignKey('person.id')),
     Column('object_id', Integer,default=0),
     Column('object_type', DBString(60)),
     Column('value', DBText),
     Column("approved", Boolean, default=False),
     Column("created", DateTime,default=datetime.now),
)
class Version(ModelBase):
    schema = version
    def use_version(self,cls):
        """"""
        try:
            _json = escape.json_decode(self.value)
            obj = cls.saget(_json['id'])
            obj.from_dict(_json)
            return obj
        except ValueError:
            log.error("could not decode json for cls=%s, json=%s" % (cls,self.value))
            return None
    
    @classmethod
    def create_version(cls,obj,user,expunge=False):
        'creates version of obj'
        jsons = obj.to_json()
        versionct = 0
        v = Version()
        v.object_id = obj.id
        if expunge:
            meta.DBSession.refresh(obj)
            #v._session.expunge(obj)'
        if obj.version_latest and obj.version_latest.id > 0:
            versionct = obj.version_latest.version + 1
        cls_name = str(obj.__class__)
        cls_name = cls_name[cls_name.rfind('.')+1:cls_name.rfind('\'')].lower()
        v.object_type = cls_name
        v.person_id = user.id
        v.value = jsons
        v.version = versionct
        v.save()
        return v
    


class VersionMixin(object):
    def _set_version(self, version):
        if version:
            self._version = version
        else:
            self._version = version
    
    def _get_version(self):
        if hasattr(self,'_version'):
            return self._version
        cls_name = str(self.__class__)
        cls_name = cls_name[cls_name.find('.')+1:cls_name.rfind('\'')].lower()
        self._version = self._session.query(Version).filter(and_(Version.object_id == self.id,Version.object_type==cls_name)).first()
        return self._version
    
    version = property(_get_version, _set_version)

def versionable(cls,name):
    """Versionable Mixin/Mutator"""
    mapper = class_mapper(cls)
    table = mapper.local_table
    cls_name = str(cls)
    cls_name = cls_name[cls_name.rfind('.')+1:cls_name.rfind('\'')].lower()
    mapper.add_property('versions', dynamic_loader(Version, 
        primaryjoin=and_(table.c.id==version.c.object_id,version.c.object_type==cls_name),
        foreign_keys=[version.c.object_id],
        backref='%ss' % table.name))
    
    
    # most recent version
    def version_latest(self):
        if self.versions is None:
            return None
        return self.versions.order_by(version.c.version.desc()).first()
    setattr(cls, "version_latest", property(version_latest))


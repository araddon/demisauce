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

configattribute_table = Table('configattribute', meta.metadata,
    Column('id', Integer, primary_key=True),
    Column('object_id', Integer,default=0),
    Column('object_type', DBString(30)),
    Column('name', DBString(80)),
    Column("value", DBString(1000)),
    Column('category', DBString(30)),
    Column('event_type', DBString(30)),
    Column('encoding', DBString(10),default="str"),
    Column("created", DateTime,default=datetime.now),
    Column("requires", DBString(1000)),
)

class ConfigAttribute(ModelBase,SerializationMixin): 
    _allowed_api_keys = ['name','value','encoding','category','requires','object_type','event_type','object_id']
    _readonly_keys = ['id','created','datetime_created']
    schema = configattribute_table

class ConfigMixin(object):
    """"""
    def get_attributes(self,category=None):
        pass
    
    def get_attribute(self,name):
        """Returns the ConfigAttribute object for given name"""
        for attribute in self.settings:
            if attribute.name == name:
                if attribute.encoding == 'json' and isinstance(attribute.value,(str,unicode)):
                    attribute.value = json.loads(attribute.value)
                return attribute
        return None
    
    def get_val(self,name):
        attr = self.get_attribute(name)
        if attr:
            return attr.value
        return None
    
    def has_attribute(self,name):
        """Returns True/False if it has given key attribute"""
        for attribute in self.settings:
            if attribute.name == name:
                return True
        return False
    
    def has_attribute_value(self,name,value):
        """Returns True/False if it has given key/value pair attribute"""
        for attribute in self.settings:
            if attribute.name == name and value == attribute.value:
                return True
        return False
    
    def add_attribute(self,name,value,object_type=None,category="segment",encoding='str',requires=None,event_type=None):
        """Add or Update attribute """
        attr = self.get_attribute(name)
        if isinstance(value,(dict,list)) or encoding == 'json':
            value = json.dumps(value)
            encoding = 'json'
        if attr:
            attr.encoding   = encoding
            attr.value      = value
            attr.event_type = event_type
            attr.category   = category
            attr.requires   = requires
            return attr
        else:
            cls_name = str(self.__class__)
            cls_name = cls_name[cls_name.rfind('.')+1:cls_name.rfind('\'')].lower()
            attr = ConfigAttribute(object_type=cls_name,event_type=event_type,
                name=name,value=value,category=category,encoding=encoding,requires=requires)
            if self._is_cache:
                attr.object_id = self.id
                meta.DBSession().commit(attr)
            else:
                if self.id > 0:
                    attr.object_id = self.id
                self.settings.append(attr)
            return attr
        return None
    

def config_keyable(cls,name="settings"):
    """Object - List Mixin/Mutator"""
    mapper = class_mapper(cls)
    table = mapper.local_table
    cls_name = str(cls)
    cls_name = cls_name[cls_name.rfind('.')+1:cls_name.rfind('\'')].lower()
    mapper.add_property(name, dynamic_loader(ConfigAttribute, 
        primaryjoin=and_(table.c.id==configattribute_table.c.object_id,configattribute_table.c.object_type==cls_name),
        foreign_keys=[configattribute_table.c.object_id],
        backref='%s' % table.name))
    
    # initialize some stuff
    def on_new(self):
        self.object_type = cls_name
    setattr(cls, "on_new", on_new)
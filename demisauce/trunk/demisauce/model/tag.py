from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.sql import and_, select, func
from sqlalchemy.types import Integer, String as DBString, \
    DateTime, Text as DBText, Boolean
from sqlalchemy.orm import mapper, relation, MapperExtension, EXT_PASS
from sqlalchemy.orm import class_mapper
from demisauce.model import ModelBase, meta
from demisauce.model.site import Site
from demisauce.model.person import Person

import logging, urllib
import formencode
from formencode import validators
from datetime import datetime
import simplejson



tag_table = Table("tag", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column('site_id', None, ForeignKey('site.id')),
        Column('assoc_id', None, ForeignKey('tag_map.id')),
        Column('person_id', None, ForeignKey('person.id')),
        Column("value", DBString(40), nullable=False),
    )
## map table
tag_map_table = Table("tag_map", meta.metadata,
    Column('id', Integer, primary_key=True),
    Column('type', DBString(50), nullable=False),
    Column('version', Integer, default=0),
)

class Tag(ModelBase):
    """
    :tag: tag (no whitespace or illegal character)
    :person:  person
    """
    def __init__(self,**kwargs):
        super(Tag, self).__init__(**kwargs)
        if 'tag' in kwargs:
            self.value = kwargs['tag']
        if 'person' in kwargs:
            person = kwargs['person']
            self.person_id = person.id
            self.username = person.displayname
            self.site_id = person.site_id
    
    member = property(lambda self: getattr(self.association, '_backref_%s' % self.association.type))
    
    @classmethod
    def by_key(self,site_id=0,tag_type=None):
        """get all tags for a specific type"""
        s = select([tag_table.c.value],
            from_obj=[tag_table.join(tag_map_table, tag_map_table.c.type=='help')],
            whereclause=(tag_table.c.assoc_id == tag_map_table.c.id),
            distinct=True)
        tag_list = meta.engine.execute(s)
        return [row[0] for row in tag_list]
    
    @classmethod
    def by_cloud(self,site_id=0,tag_type=None):
        """get all tags for a specific type"""
        s = select([tag_table.c.value, func.count(tag_table.c.value)],
            from_obj=[tag_table.join(tag_map_table, tag_map_table.c.type=='help')],
            whereclause=(tag_table.c.assoc_id == tag_map_table.c.id),
            group_by=[tag_table.c.value],
            order_by=[tag_table.c.value])
        tag_list = meta.engine.execute(s)
        return [row for row in tag_list]

class TagAssoc(object):
    """
    :type: the table/type this is associated with
        since this can relate to multiple table/entity types, 
        this lists which type this is related to
    """
    def __init__(self, name):
        self.type = name
    

def taggable(cls, name, uselist=True):
    """taggable 'interface'.
    """
    import demisauce.model.person
    mapper = class_mapper(cls)
    table = mapper.local_table
    mapper.add_property('tag_rel', relation(TagAssoc, 
        cascade="save-update, merge,refresh-expire",
        backref='_backref_%s' % table.name))

    if uselist:
        # list based property decorator
        def get(self):
            if self.tag_rel is None:
                self.tag_rel = TagAssoc(table.name)
            return self.tag_rel.tags
        setattr(cls, name, property(get))
    else:
        # scalar based property decorator
        def get(self):
            return self.tag_rel.tags[0]
        def set(self, value):
            if self.tag_rel is None:
                self.tag_rel = TagAssoc(table.name)
            self.tag_rel.tags = [value]
        setattr(cls, name, property(get, set))


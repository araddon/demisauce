from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.sql import and_
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
temp = """ 
change_table = Table("changes", metadata,
        Column("id", Integer, primary_key=True),
        Column('assoc_id', None, ForeignKey('change_associations.assoc_id')),
        Column("change", DBString(255), nullable=False),
        Column("site_id", Integer),
        Column("person_id", Integer, ForeignKey('person.id')),
        Column("link", DBString(255), default=''),
        Column("created", DateTime,default=func.now()),
        Column("node_id", Integer),
        Column("username", DBString(50), default=''),
    )
## association table
change_associations_table = Table("change_associations", metadata,
    Column('assoc_id', Integer, primary_key=True),
    Column('type', DBString(50), nullable=False),
    Column('version', Integer, default=0),
)
class TagExt(MapperExtension):
    def before_update(self, mapper, connection, instance):
        #connection.execute(member_table.delete(member_table.c.org_id==instance.org_id))
        #print 'in before update, does this hit inserts?'
        instance._dochanges()
        return EXT_PASS

    def before_insert(self, mapper, connection, instance):
        #connection.execute(member_table.delete(member_table.c.org_id==instance.org_id))
        print 'in before insert, does this hit updates? type=%s' % dir(instance)
        instance._dochanges()
        return EXT_PASS
"""

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
    mapper.add_property('tag_rel', relation(TagAssoc, backref='_backref_%s' % table.name))

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


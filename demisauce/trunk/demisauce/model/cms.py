#!/usr/bin/env python
from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.types import Integer, String as DBString, DateTime
from sqlalchemy.types import Text as DBText
from sqlalchemy.orm import mapper, relation, MapperExtension, EXT_CONTINUE
from demisauce import model
#from demisauce.model import mapping
from demisauce.model import meta, ModelBase
from datetime import datetime

cmsitem_table = Table("cms", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, default=1),
        Column("children_count", Integer,default=1),
        Column("created", DateTime,default=datetime.now),
        Column("last_update",DateTime,default=datetime.now,onupdate=datetime.now),
        Column("item_type", DBString(20), default='cms'),
        Column("title", DBString(120), nullable=False),
        Column("key", DBString(150), nullable=False),
        Column("rid", DBString(255), nullable=True),
        Column("url", DBString(255), nullable=True),
        Column("content", DBText, default=''),
        Column("content2", DBText, default=''),
        Column("tags", DBString(500), nullable=True),
    )

cms_associations_table = Table('cmslinks', meta.metadata,
        Column("id", Integer, primary_key=True),
        Column('parent_id', Integer, ForeignKey('cms.id')),
        Column('child_id', Integer, ForeignKey('cms.id')),
        Column("position", Integer,default=1),
    )

def get_by_title(title):
    """
    Gets a set of content by title
    """
    return meta.DBSession.query(Cmsitem).filter_by(title=title).first()



class Cmsassoc(object):
    def __init__(self,child):
        self.item = child
    

class Cmsitem(ModelBase):
    """
    
        >>> c = Cmsitem('test docstring title', 'some mixed<b>content</b>',1)
        >>> c.save()
        >>> c.title
        'test dostring title'
        >>> c.key
        'test_docstring_title'
    
    """
    def __init__(self, site_id, title, content):
        self.title = title
        self.content = content
        self.key = self.makekey(title)
        self.rid = self.key
        self.site_id = site_id
    
    def addChild(self,childItem):
        ca = Cmsassoc(childItem)
        self.children.append(ca)
        ca.position = len(self.children)
    
    def __onupdate__(self):
        self.last_update = datetime.now()
        pass
    
    def delete(self):
        for cmsassoc in self.parents:
            meta.DBSession.delete(cmsassoc)
        meta.DBSession.delete(self)
        meta.DBSession.commit()
    
    def __str__(self):
        return self.title
    
    def get_cleancontent(self):
        '''clean up the content'''
        return self.content.replace('\n',' \\').replace('\r','').replace('\\',''
            ).replace('\'',"\\'")
    
    clean_content = property(get_cleancontent)
    
    @classmethod
    def get_root(cls,site_id):
        """Class method to get the root content"""
        return meta.DBSession.query(Cmsitem).filter_by(site_id=site_id,
            item_type='root').first()
    


class CmsMapperExt(MapperExtension):
    """will update children count etc"""
    def before_update(self, mapper, connection, instance):
        #instance.__onupdate__()
        return EXT_CONTINUE
    



import logging
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.types import Integer, String as DBString, Boolean
from sqlalchemy.types import Text as DBText, DateTime
from demisauce import model
from demisauce.model import meta, ModelBase, site, JsonMixin
from datetime import datetime
import json

# Define a table.
object_table = Table("object", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("person_id", Integer, ForeignKey('person.id')),
        Column("foreign_id", Integer, default=0, index=True),
        Column("displayname", DBString(80)),
        Column("post_type", DBString(20), nullable=False, index=True,default="post"),
        Column("slug", DBString(50), nullable=False, index=True),
        Column("description", DBString(120), nullable=True),
        Column("json", DBText, nullable=True),
        Column("created", DateTime,default=datetime.now),
        Column("is_published", Boolean, default=False),
)

class Object(ModelBase,JsonMixin):
    schema = object_table
    _allowed_api_keys = ['slug','description','json','is_published']
    def __init__(self, **kwargs):
        super(Object, self).__init__(**kwargs)
    
    def from_dict(self,json_dict={},allowed_keys=None):
        new_dict = json_dict
        new_dict.pop('apikey')
        json_dict.update({'json':json.dumps(new_dict)})
        super(Object, self).from_dict(json_dict=json_dict,allowed_keys=allowed_keys)
    
    @classmethod
    def all(cls,site_id=0):
        return meta.DBSession.query(Object).filter_by(site_id=site_id)
    
    @classmethod
    def by_slug(cls,site_id=0,slug=''):
        qry = meta.DBSession.query(Object).filter_by(site_id=site_id,slug=slug)
        logging.debug('qry = %s, slug="%s"' % (qry,slug))
        return qry.first()
    

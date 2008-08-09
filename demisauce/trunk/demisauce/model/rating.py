from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.sql import and_
from sqlalchemy.types import Integer, String as DBString, DateTime, \
   Text as DBText, Boolean
from demisauce.model import ModelBase, meta
from demisauce.model import site
from demisauce import model
from datetime import datetime


rating_table = Table("rating", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("person_id", Integer, default=0),
        Column("obj_id", Integer),
        Column("entry", Integer),
        Column("created", DateTime,default=datetime.now()),
        Column("username", DBString(50)),
        Column("type", DBString(255)),
    )

class Rating(object,ModelBase):
    """
    rating allow 
    
    :person_id: (optional) id of the person
    :type: string defining the "context" '/ds/help/article' (arbitrary string) but suggested
        that you do /appname/entity type/specifier
    :entry: vote down = -1, vote up = 1, room for other options
    :obj_id:   foreign key value (integer) of entity id in foreign db
    :created:  date created
    
    """
    def __init__(self, person_id = 0,rating_type='/help/article',entry=-1,obj_id=0, username=""):
        """
        Init create a rating object to add a rating::
            
            helpitem.rating_ct += 1
            r = Rating(c.user.id,'/ds/help/article',1,helpitem.id,c.user.displayname)
        """
        self.person_id = person_id
        self.entry = entry
        self.username = username
        self.type = rating_type
        self.obj_id = obj_id
    


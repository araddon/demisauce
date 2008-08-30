from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.types import Integer, String as DBString, DateTime, \
    Text as DBText, Boolean, SmallInteger
from sqlalchemy.sql import func, select, text
from demisauce import model
from demisauce.model import meta, ModelBase
from datetime import datetime

activity_table = Table("activity", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("person_id", Integer, ForeignKey('person.id')),
        Column("activity", DBString(255)),
        Column("category", DBString(50)),
        Column("custom1name", DBString(15)),
        Column("custom1val", DBString(50)),
        Column("custom2name", DBString(15)),
        Column("custom2val", DBString(50)),
        Column("ref_url", DBString(500)),
        Column("created", DateTime),
        Column("year",Integer,default=0),
        Column("month",Integer,default=0),
        Column("day",Integer,default=0)
    )

class Activity(ModelBase):
    def __init__(self, site_id, person_id, activity=None):
        self.site_id = site_id
        self.person_id = person_id
        self.activity = activity
        self.created = datetime.now()
        self.year = self.created.year
        self.month = self.created.month
        self.day = self.created.day
    
    @classmethod
    def by_activity(cls,site_id=0,activity=None):
        """Class method to get site by slug"""
        return meta.DBSession.query(Activity).filter_by(site_id=site_id,activity=activity).all()
    
    @classmethod
    def by_person(cls,site_id=0,person_id=0,ct=50):
        return meta.DBSession.query(Activity).filter_by(
            site_id=site_id,person_id=person_id).limit(ct)
    
    @classmethod
    def recent_users(cls,site_id=0):
        #q = text("""SELECT count(id), activity FROM activity where person_id=1 group by month, activity""")
        q = text("""SELECT count(id) as ct, person_id, activity FROM activity where site_id=%s group by activity order by ct desc""" % person_id)
        res = meta.engine.execute(q)
        act = [a for a in res]
        return act
    
    @classmethod
    def activity_by_person(cls,site_id=0,person_id=0):
        #q = text("""SELECT count(id), activity FROM activity where person_id=1 group by month, activity""")
        q = text("""SELECT count(id) as ct, activity FROM activity where person_id=%s group by activity order by ct desc""" % person_id)
        res = meta.engine.execute(q)
        act = [a for a in res]
        return act
    
    @classmethod
    def categories(cls,site_id=0,person_id=0):
        #q = text("""SELECT count(id), activity FROM activity where person_id=1 group by month, activity""")
        q = text("""SELECT count(id) as ct, category FROM activity where person_id=%s AND category not NULL group by category order by ct desc""" % person_id)
        res = meta.engine.execute(q)
        act = [a for a in res]
        return act
    
    @classmethod
    def stats_by_person(cls,site_id=0,person_id=0):
        #q = text("""SELECT count(id), activity FROM activity where person_id=1 group by month, activity""")
        q = text("""SELECT count(id), day, month, year FROM activity where person_id=%s group by year,month,day""" % person_id)
        res = meta.engine.execute(q)
        act = [a for a in res]
        return act
    


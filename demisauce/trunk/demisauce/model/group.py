from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.sql import and_
from sqlalchemy.types import Integer, String as DBString, DateTime, \
   Text as DBText, Boolean
from demisauce.model import ModelBase, meta
from demisauce.model import site

import logging, string
import formencode
from formencode import validators
from datetime import datetime
from demisauce.model import person

# DB Table:  group ---------------------------
group_table = Table("group", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("author_id", Integer, nullable=True,default=0),
        Column("created", DateTime,default=datetime.now),
        Column("group_type", DBString(30), default='groups'),
        Column("name", DBString(255), nullable=False),
        Column("description", DBString(500)),
        Column("contacts", DBText),
        Column("public", Boolean, default=False),
    )
groupperson_table = Table('person_group', meta.metadata,
    Column('group_id', Integer, ForeignKey('group.id')),
    Column('person_id', Integer, ForeignKey('person.id')),
)


class Group(ModelBase):
    """
    group
    
    :name: name of this group
    :email_list: comma delimited list of email address's of this group
    :members: List of person objects
    :created:  date created
    :description: description
    """
    def __init__(self,site_id, name='', description=""):
        self.name = name
        self.description = description
        self.site_id = site_id
        #self.__members = []
        self.group_type == 'node'
    
    def get_email_list(self):
         return ', '.join(['%s' % m.email.strip(string.whitespace).lower() for m in self.members])
    email_list = property(get_email_list)
        
    def add_memberlist(self,member_list):
        """
        Accepts a comma delimited list of contacts
        
        returns a tuple of lists, first of new users not already in this group
        2nd of users newly added to system
        """
        #ml = [m.strip(string.whitespace) for m in member_list.replace(';',',').split(',') if len(m) > 4]
        ml_temp = member_list.replace(';',',').lower()
        cl = [ e.strip(string.whitespace) for e in ml_temp.split(',') if len(e) > 5]
        
        ml = ['%s' % m.email.strip(string.whitespace).lower() for m in self.members]
        
        newlist = [e for e in cl if not ml.__contains__(e.strip(string.whitespace))]
        
        removelist = [e for e in ml if not cl.__contains__(e.strip())]
        [self.remove_member(e) for e in removelist]
        addedusers = [self.add_member(e) for e in newlist]
        newtosite = [e for e in addedusers if e != None]
        newtogroup = [e for e in newlist if not addedusers.__contains__(e)]
        #self.contacts = ','.join(self.__members)
        return newtogroup, newtosite  
    
    def remove_member(self, newemail):
        """
        removes a user
        """
        [self.members.remove(p) for p in self.members if p.email.lower() == newemail]
    
    def member_byemail(self, email):
        """
        returns a user from members list that has given email?
        """
        for p in self.members:
            if p.email.lower() == email:
                return p
        
        return None
    
    def add_member(self, newemail):
        # don't trust this user is new
        p = person.Person.by_email(self.site_id,newemail)
        if p and p.id > 0:
            self.members.append(p)
        else:
            self.members.append(person.Person(site_id=self.site_id,email=newemail))
            return newemail
    
    @classmethod
    def by_site(cls,site_id=0,ct=15,filter='new'):
        """Class method to get groups"""
        return meta.DBSession.query(Group).filter_by(
            site_id=site_id).order_by(group_table.c.created.desc()) #.limit(ct)

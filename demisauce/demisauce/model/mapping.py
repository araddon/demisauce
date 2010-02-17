"""
Map different model files together, process in correct order for
dependency issues.
"""
#  this pre-compiles all the db modules
from sqlalchemy.orm import mapper, relation, dynamic_loader
from sqlalchemy.sql import and_
from demisauce.model.site import site_table, Site
from demisauce.model.user import person_table, Person, Group, groupperson_table, group_table
from demisauce.model.email import *
from demisauce.model.object import Object, object_table
#from demisauce.model.comment import Comment, comment_table
#from demisauce.model.help import Help, help_table, \
#        HelpResponse, help_response_table
from demisauce.model.activity import Activity, activity_table
from demisauce.model.service import App, app_table, Service, service_table
from demisauce.model.tag import Tag, TagAssoc, taggable, tag_table, \
    tag_map_table

mapper(Site, site_table)

mapper(Group, group_table, properties={
    'site':relation(Site, backref='groups')
})
mapper(Activity, activity_table, properties={
    'site':relation(Site, lazy=True, order_by=activity_table.c.created.desc(),
        backref='activities'),
})
mapper(Tag, tag_table, properties={
    'site':relation(Site, lazy=True, backref='tags'),
})

mapper(TagAssoc, tag_map_table, properties={
    'tags':relation(Tag, backref='association'),
})
mapper(Person, person_table, properties={
    'site':relation(Site, backref='users'),
    'groups':relation(Group, lazy=True, secondary=groupperson_table,
            primaryjoin=person_table.c.id==groupperson_table.c.person_id,
            secondaryjoin=and_(groupperson_table.c.group_id==group_table.c.id), 
                        backref='members'),
    'activities':dynamic_loader(Activity),
    'tags':relation(Tag,lazy=True,backref='taggers')
})
'''

mapper(Help, help_table, properties={
    'site':relation(Site, lazy=True, order_by=help_table.c.created.desc(),
        backref='helptickets'),
})
mapper(HelpResponse, help_response_table, properties={
    'site':relation(Site, lazy=True, order_by=help_response_table.c.created.desc(),
        backref='helpreponses'),
    'person':relation(Person, lazy=True, backref='helpreponses'),
    'helpticket':relation(Help, backref='helpresponses'),
})
taggable(Help, 'tags', uselist=True)
mapper(Comment, comment_table, properties={
    'site':relation(Site, backref='comments')
})
'''
mapper(Email, email_table, properties={
    'site':relation(site.Site),
})
mapper(Object, object_table, properties={
    'site':relation(site.Site),
    'person':relation(Person, lazy=True, backref='objects'),
})


mapper(App, app_table, properties={
    'site':relation(Site, backref='apps'),
    'owner':relation(Person, lazy=True, backref='apps'),
})

mapper(Service, service_table, properties={
    'site':relation(Site, backref='services'),
    'owner':relation(Person, lazy=True, backref='services'),
    'app':relation(App, backref='services')
})

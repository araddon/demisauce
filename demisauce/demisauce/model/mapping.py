"""
Map different model files together, process in correct order for
dependency issues.
"""
#  this pre-compiles all the db modules
from sqlalchemy.orm import mapper, relation, dynamic_loader
from sqlalchemy.sql import and_
from demisauce.model.site import site_table, Site
from demisauce.model.user import person_table, Person, Group, \
    userattribute_table, group_table, userlistable, UserAttribute
from demisauce.model.template import Template, template_table
from demisauce.model.object import Object, object_table
#from demisauce.model.comment import Comment, comment_table
#from demisauce.model.help import Help, help_table, \
#        HelpResponse, help_response_table
from demisauce.model.activity import Activity, activity_table
from demisauce.model.service import App, app_table, Service, service_table
from demisauce.model.tag import Tag, TagAssoc, taggable, tag_table, \
    tag_map_table
from demisauce.model.config import ConfigAttribute, configattribute_table, \
    config_keyable
from demisauce.model.version import Version, version, versionable

mapper(Site, site_table)
mapper(ConfigAttribute, configattribute_table)
mapper(Version, version) 

config_keyable(Site,name="settings")
versionable(Site, 'versions')

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
mapper(UserAttribute, userattribute_table)
mapper(Person, person_table, properties={
    'site':relation(Site, backref='users'),
    'activities':dynamic_loader(Activity),
    'tags':relation(Tag,lazy=True,backref='taggers'),
    'attributes':dynamic_loader(UserAttribute,backref="member"),
})

userlistable(Group,name="members")


#versionable(Producer, 'versions')

mapper(Template, template_table, properties={
    'site':relation(Site),
})
mapper(Object, object_table, properties={
    'site':relation(Site),
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

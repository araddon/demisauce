"""
Map different model files together, process in correct order for
dependency issues.
"""
#  this pre-compiles all the db modules
from sqlalchemy.orm import mapper, relation, dynamic_loader
from sqlalchemy.sql import and_
from demisauce.model.site import site_table, Site
from demisauce.model.person import person_table, Person
from demisauce.model.cms import *
from demisauce.model.email import *
from demisauce.model.group import Group, groupperson_table, group_table
from demisauce.model.comment import Comment, comment_table
from demisauce.model.help import Help, help_table, \
        HelpResponse, help_response_table
from demisauce.model.activity import Activity, activity_table
from demisauce.model.poll import Poll, Question, QuestionOption, \
    PollResponse, PollAnswer, poll_table, question_table, \
    question_option_table, poll_response_table, answer_table
from demisauce.model.rating import Rating, rating_table
from demisauce.model.service import App, app_table, Service, service_table
from demisauce.model.tag import Tag, TagAssoc, taggable, tag_table, \
    tag_map_table

mapper(Site, site_table)

mapper(Group, group_table, properties={
    'site':relation(Site, backref='groups')
})
mapper(Cmsitem, cmsitem_table, extension=CmsMapperExt(), properties={
    'children':relation(Cmsassoc, lazy=True, 
            primaryjoin=cmsitem_table.c.id==cms_associations_table.c.parent_id,
            order_by=cms_associations_table.c.position.asc(),
                        backref='parent'),
})
mapper(Cmsassoc, cms_associations_table, properties={
    'item':relation(Cmsitem,lazy=False, join_depth=2,
            primaryjoin=cms_associations_table.c.child_id==cmsitem_table.c.id,
                        backref='parents'),
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

mapper(Email, email_table, properties={
    'site':relation(site.Site),
})
mapper(Comment, comment_table, properties={
    'site':relation(Site, backref='comments')
})
# -----   Poll's
mapper(Poll, poll_table, order_by=poll_table.c.created.desc(), properties={
    'site':relation(Site, backref='polls'),
    'author':relation(Person,backref='polls')
})
mapper(Question, question_table, properties={
    'poll':relation(Poll, backref='questions')
})
mapper(QuestionOption, question_option_table, order_by=question_option_table.c.sort_order.asc(), properties={
    'question':relation(Question, backref='options')
})
mapper(PollResponse, poll_response_table, properties={
    'poll':relation(Poll, backref='responses')
})
mapper(PollAnswer, answer_table, properties={
    'response':relation(PollResponse, backref='answers'),
    'option':relation(QuestionOption, backref='answers'),
    'question':relation(Question, lazy=True, backref='answers')
})

mapper(Rating, rating_table)

mapper(App, app_table, properties={
    'site':relation(Site, backref='apps'),
    'owner':relation(Person, lazy=True, backref='apps'),
})

mapper(Service, service_table, properties={
    'site':relation(Site, backref='services'),
    'owner':relation(Person, lazy=True, backref='services'),
    'app':relation(App, backref='services')
})

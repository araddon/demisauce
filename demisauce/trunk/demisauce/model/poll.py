from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table
from sqlalchemy.sql import and_
from sqlalchemy.types import Integer, String as DBString, \
    DateTime, Text as DBText, Boolean
from demisauce.model import ModelBase, meta
from demisauce.model.site import Site
from demisauce.model.person import Person

import logging, urllib
import formencode
from formencode import validators
from datetime import datetime
import simplejson


poll_table = Table("poll", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("person_id", Integer, ForeignKey('person.id')),
        Column("created", DateTime,default=datetime.now()),
        Column("response_count", Integer, default=0),
        Column("allow_anonymous", Boolean, default=False),
        Column("name", DBString(255), nullable=False),
        Column("key", DBString(150), nullable=False),
        Column("description", DBString(500)),
        Column("css", DBString(1000)),
        Column("html", DBText),
        Column("json", DBText),
    )

question_table = Table("poll_question", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("poll_id", Integer, ForeignKey('poll.id')),
        Column("question", DBString(255), nullable=False),
        Column("type", DBString(20),nullable=False,default='radiowother'),
        Column("question", DBString(255), nullable=False),
    )

question_option_table = Table("poll_question_option", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("question_id", Integer, ForeignKey('poll_question.id')),
        Column("sort_order", Integer, default=1),
        Column("count", Integer, default=0),
        Column("type", DBString(10),nullable=False,default='radio'),
        Column("option", DBString(255), nullable=False),
    )

poll_response_table = Table("poll_response", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("poll_id", Integer, ForeignKey('poll.id')),
        Column("person_id", Integer, default=0),
        Column("created", DateTime,default=datetime.now()),
    )

answer_table = Table("poll_answer", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("poll_response_id", Integer, ForeignKey('poll_response.id')),
        Column("question_id", Integer, ForeignKey('poll_question.id')),
        Column("option_id", Integer, ForeignKey('poll_question_option.id')),
        Column("other", DBString(500)),
    )


class Poll(object,ModelBase):
    """
    Poll (or survey), a collection of questions to be asked, either
    to known people or anonymously
    
    
    allow_anonymous:   Allow anonymous poller's  (default=false)
    html:   Allows the html for the poll to be cached to cheat a bit
    author:  Creator person object of poll
    """
    def __init__(self,site_id=0, name='', description=""):
        self.name = name
        self.description = description
        self.site_id = site_id
        
    
    def get_url_encoded_name(self):
        return urllib.quote_plus(self.name)
    url_name = property(get_url_encoded_name)
    
    def get_question_ids(self):
        return ','.join([str(q.id) for q in self.questions])
    question_ids = property(get_question_ids)
    
    def get_question(self,id):
        """return question if it exists for specific id"""
        for q in self.questions:
            if q.id == id:
                return q
        
        return None
    
    def update_vote(self,response):
        """update the vote count cache"""
        self.response_count += 1
        for a in response.answers: 
            a.option.count += 1
        self.save()
    
    @classmethod
    def by_key(cls,site_id=0,key=''):
        """
        Gets the template by key for a site::
            
            Poll.by_key(c.site_id,'what_features_do_we_want_in_demisauce')
        """
        return meta.DBSession.query(Poll).filter_by(site_id=site_id,key=key).first()
    
    @classmethod
    def by_site(cls,site_id=0):
        """
        Gets list of all polls for a site (could be large)
        """
        return meta.DBSession.query(Poll).filter_by(site_id=site_id).all()
    
    @classmethod
    def by_name(cls,site_id=0,name=''):
        """
        Gets list of a poll by name::
            
            Poll.by_name(c.site_id,'What features do we want in Demisauce?')
        """
        q = meta.DBSession.query(Poll).filter_by(site_id=site_id,name=str(name)).all()
        return q
    

class Question(object,ModelBase):
    """
    A poll has one or more questions
    
    type:  radio,multiplechoice,radiowother
    """
    def __init__(self, question,question_type='radio'):
        self.question = question
        self.type = question_type
        self.max_sort_order = -1
        self.update_sort_order()
    
    def update_sort_order(self):
        """updates the max sort order"""
        self.max_sort_order = -1
        for o in self.options:
            if self.max_sort_order < o.sort_order:
                self.max_sort_order = o.sort_order
    
    def change_sort_order(self,oid,sort_order):
        """accepts an ordered list of option ids
        and then updates their sort order"""
        for o in self.options:
            if o.id == int(oid):
                o.sort_order = sort_order
        return None
    
    def get_option(self,id):
        """return option if it exists for specific id"""
        for o in self.options:
            if o.id == id:
                return o
        return None
    
    def add_or_update_option(self,option,o_id=0):
        """add or update option"""
        if hasattr(self,'max_sort_order') == False:
            self.update_sort_order()
        o = None
        if o_id > 0:
            o = self.get_option(o_id)
            o.option = option
        else:
            exists = [o for o in self.options if (o.option == option)]
            if exists == [] and option != '':
                o = QuestionOption(option)
                self.max_sort_order += 1
                o.sort_order = self.max_sort_order
                self.options.append(o)
        
        return o
    

class QuestionOption(object,ModelBase):
    """
    Each question has a list of choices(options)
    
    type:  radio,other(text),check
    """
    def __init__(self, option,option_type='radio'):
        super(QuestionOption, self).__init__()
        self.option = option
        self.type = option_type
    

class PollResponse(object,ModelBase):
    """
    The response by person (or anonymous), will have a collection of answers
    """
    def __init__(self, person_id=0):
        self.person_id = person_id
    

class PollAnswer(object,ModelBase):
    """
    Each person (optionally) answer's each qustion
    """
    def __init__(self,question_id,option_id,other=''):
        super(PollAnswer, self).__init__()
        self.question_id = question_id
        self.option_id = option_id
        self.other = other
    


#!/usr/bin/env python
import logging
import urllib
from tornado.options import options
from demisauce import model
from demisauce.model import meta, mapping, activity
from demisauce.model.user import Person
from demisauce.model.activity import Activity
from demisauce.model.site import Site
from demisauce.controllers import BaseHandler, RestMixin, SecureController

log = logging.getLogger(__name__)


class DashboardController(RestMixin, SecureController):
    def index(self,id=0):
        items = None
        if self.user and self.user.issysadmin:
            items = meta.DBSession.query(Site).all()
        
        #if self.user:
        #    qry = model.help.Help.by_site(self.user.site_id)
        #    new_ticket_ct = qry.count()
        #    helptickets = qry.limit(5)
        #    comments = Comment.by_site(self.user.site_id).limit(5)
        #,helptickets=helptickets,comments=comments,new_ticket_ct=new_ticket_ct
            
        self.render('/dashboard.html',items=items)
    

class ActivityController(RestMixin, SecureController):
    def index(self,id=''):
        if id > 0:
            person = Person.get(self.user.site_id,id)
            activities = Activity.activity_by_person(self.user.site_id,id)
            activities_by_day = Activity.stats_by_person(self.user.site_id,id)
            categories = Activity.categories(self.user.site_id,id)
            return self.render('/activity.html',person=person,activities=activities,
                activities_by_day=activities_by_day,categories=categories)
        else:
            self.write("no id?  %s" % id)
    

_controllers = [
    (r"/dashboard(?:\/)?(.*?)", DashboardController),
    (r"/activity/(.*?)/(.*?)", ActivityController),
]

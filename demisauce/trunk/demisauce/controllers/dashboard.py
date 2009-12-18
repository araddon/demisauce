#!/usr/bin/env python
import logging
import urllib
from formencode import Invalid, validators
import formencode

from demisauce import model
from demisauce.model import meta, mapping, activity
from demisauce.model.person import Person
from demisauce.model.site import Site
from demisauce.model.comment import Comment
from demisauce.controllers import BaseHandler, RestMixin, SecureController

log = logging.getLogger(__name__)


class DashboardController(RestMixin, SecureController):
    def index(self,id=0):
        items = None
        if self.user and self.user.issysadmin:
            items = meta.DBSession.query(Site).all()
        if self.user:
            qry = model.help.Help.by_site(self.user.site_id)
            new_ticket_ct = qry.count()
            helptickets = qry.limit(5)
            comments = Comment.by_site(self.user.site_id).limit(5)
            
        self.render('/dashboard.html',items=items,helptickets=helptickets,
            comments=comments,new_ticket_ct=new_ticket_ct)
        
    
_controllers = [
    (r"/dashboard(?:\.)?(.*?)", DashboardController),
]

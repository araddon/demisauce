#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import meta, mapping, activity
from demisauce.model.person import Person
from demisauce.model.site import Site
from demisauce.model.comment import Comment

log = logging.getLogger(__name__)


class DashboardController(SecureController):
    
    def index(self):
        if c.user and c.user.issysadmin:
            c.items = meta.DBSession.query(Site).all()
        if c.user:
            c.helptickets = model.help.Help.by_site(c.user.site_id,5)
            c.new_ticket_ct = model.help.Help.new_tickets_ct(c.user.site_id)
            c.comments = Comment.by_site(c.user.site_id,5)
            
        return render('/dashboard.html')
        
    


#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
from sqlalchemy.orm import eagerload

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import site, person
from demisauce.model.activity import Activity
from paste.httpexceptions import HTTPException
from paste.wsgiwrappers import WSGIResponse


log = logging.getLogger(__name__)

class ActivityController(SecureController):
    def index(self,id=''):
        if id > 0:
            c.person = person.Person.get(c.user.site_id,id)
            c.activities = Activity.activity_by_person(c.user.site_id,id)
            c.activities_by_day = Activity.stats_by_person(c.user.site_id,id)
            c.categories = Activity.categories(c.user.site_id,id)
        return render('/activity.html')
    



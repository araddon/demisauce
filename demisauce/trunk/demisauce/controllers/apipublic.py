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
from demisauce.model import site, activity, person
from paste.httpexceptions import HTTPException
from paste.wsgiwrappers import WSGIResponse


log = logging.getLogger(__name__)

class ApipublicController(BaseController):
    def activity(self,id=''):
        if not c.user and 'hashedemail' in request.params: 
            user = person.Person.by_hashedemail(str(request.params['hashedemail']))
        elif c.user:
            user = c.user
        else:
            return ''
        if 'site_slug' in request.params:
            site_slug = str(request.params['site_slug'])
        if 'activity' in request.params:
            action = str(request.params['activity'])
        a = activity.Activity(site_id=user.site_id,person_id=user.id,activity=action)
        if 'ref_url' in request.params:
            a.ref_url = request.params['ref_url']
        if 'category' in request.params:
            a.category = request.params['category']
        if 'cnames' in request.params:
            names = [n for n in request.params['cnames'].split(',') if n != '']
            if len(names) > 0:
                a.custom1name = names[0]
                a.custom1val = request.params[names[0]]
            if len(names) > 1:
                a.custom2name = names[1]
                a.custom2val = request.params[names[1]]
        a.save()
        return a.id
    



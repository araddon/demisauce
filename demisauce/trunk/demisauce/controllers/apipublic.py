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
from demisauce.model import site, activity
from paste.httpexceptions import HTTPException
from paste.wsgiwrappers import WSGIResponse


log = logging.getLogger(__name__)

class ApipublicController(BaseController):
    def activity(self,id=''):
        if c.user: # for now, must be authenticated?
            if 'site_slug' in request.params:
                site_slug = str(request.params['site_slug'])
            if 'activity' in request.params:
                action = str(request.params['activity'])
                #s = site.Site.by_slug(site_slug)
            a = activity.Activity(c.user.site_id,c.user.id,action)
            if 'ref_url' in request.POST:
                a.ref_url = request.POST['ref_url']
            if 'category' in request.POST:
                a.category = request.POST['category']
            if 'cnames' in request.POST:
                names = [n for n in request.POST['cnames'].split(',') if n != '']
                if len(names) > 0:
                    a.custom1name = names[0]
                    a.custom1val = request.POST[names[0]]
                if len(names) > 1:
                    a.custom2name = names[1]
                    a.custom2val = request.POST[names[1]]
            a.save()
            return a.id
        return ''
    




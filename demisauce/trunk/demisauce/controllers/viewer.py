#!/usr/bin/env python
import logging
from pylons import config

from demisauce.lib.base import *
from demisauce.lib.helpers import *
from demisauce import model
from demisauce.model import meta
from demisauce.model.cms import Cmsitem


log = logging.getLogger(__name__)


class ViewerController(BaseController):

    def index(self,key=''):
        if key != '':
            c.cmsitems = [meta.DBSession.query(Cmsitem).filter_by(key=key,site_id=c.site_id).first()]
        else:
            c.cmsitems = [meta.DBSession.query(Cmsitem).filter_by(site_id=c.site_id)]
        
        return render('/viewer.html')
    
    def view(self,key=''):
        return render('/simple_viewer.html')

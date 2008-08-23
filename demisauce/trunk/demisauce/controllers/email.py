"""
This is controller/email.py doc
"""
#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
#from sqlalchemy.orm import eagerload

from demisauce.lib.base import *
from demisauce import model
from demisauce.model.email import *

log = logging.getLogger(__name__)

class EmailFormValidation(formencode.Schema):
    """Form validation for the email web admin"""
    allow_extra_fields = True
    filter_extra_fields = False
    subject = formencode.All(String(not_empty=True))

class EmailController(SecureController):
    requires_auth = True
    
    #@requires_role('admin')
    @rest.dispatch_on(POST="addupdate")
    def index(self,id=0):
        if id > 0:
            c.items = [meta.DBSession.query(Email).get(id)]
        else:
            c.items = meta.DBSession.query(Email).filter_by(site_id=c.user.site_id).all()
        return render('/email.html')
    
    @validate(schema=EmailFormValidation(), form='index')
    def addupdate(self,id=0):
        if self.form_result['objectid'] == "0":
            item = Email(site_id=c.site_id, subject=self.form_result['subject'])
        else:
            id = self.form_result['objectid']
            item = meta.DBSession.query(Email).filter_by(id=id,site_id=c.site_id).first()
            item.subject = self.form_result['subject']
            
        item.template = self.form_result['template']
        item.from_name = self.form_result['from_name']
        item.from_email = self.form_result['from_email']
        item.key = self.form_result['real_permalink']
        item.to = self.form_result['to']
        item.save()
        h.add_alert('updated email template')
        return redirect_wsave('/email/index')
    
    def delete(self,id=0):
        item = Email.get(c.user.site_id,id=id)
        if item != None:
            item.delete()
        h.add_alert('deleted email template')
        return redirect_wsave('/email/index')
    
    def edit(self,id=0):
        c.item = Email.get(c.user.site_id,id=id)
        if c.item == None and (id == None or id == 0):
            c.item = Email(site_id=c.site_id,subject='')
        return render('/email.html')
        
    @requires_role('abogusrolefortesting')
    def testsecurity(self,id=0):
        """This is only for unit tests to ensure we don't have
        access as it requires a non existent role"""
        return 'failed test security'
    

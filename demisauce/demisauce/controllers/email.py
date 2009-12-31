import logging
import urllib
from formencode import Invalid, validators
from formencode.validators import *
import formencode
#from sqlalchemy.orm import eagerload
from demisauce import model
from demisauce.model.email import *
from demisauce.controllers import BaseHandler, RestMixin, SecureController, \
    requires_admin

log = logging.getLogger(__name__)

class EmailFormValidation(formencode.Schema):
    """Form validation for the email web admin"""
    allow_extra_fields = True
    filter_extra_fields = False
    subject = formencode.All(String(not_empty=True))

class EmailController(RestMixin, SecureController):
    requires_auth = True
    
    #@requires_role('admin')
    #@rest.dispatch_on(POST="addupdate")
    def index(self,id=0):
        if id > 0:
            items = [meta.DBSession.query(Email).get(id)]
        else:
            items = meta.DBSession.query(Email).filter_by(site_id=self.user.site_id).all()
        self.render('email.html',items=items)
    
    #@validate(schema=EmailFormValidation(), form='index')
    def addupdate(self,id=0):
        if self.form_result['objectid'] == "0":
            item = Email(site_id=self.user.site_id, subject=self.form_result['subject'])
        else:
            id = self.form_result['objectid']
            item = meta.DBSession.query(Email).filter_by(id=id,site_id=self.user.site_id).first()
            item.subject = self.form_result['subject']
            
        item.template = self.form_result['template']
        item.from_name = self.form_result['from_name']
        item.from_email = self.form_result['from_email']
        item.slug = self.form_result['real_permalink']
        item.to = self.form_result['to']
        item.save()
        self.add_alert('updated email template')
        return self.redirect('/email/index')
    
    def delete(self,id=0):
        item = Email.get(self.user.site_id,id=id)
        if item != None:
            item.delete()
        self.add_alert('deleted email template')
        return self.redirect('/email/index')
    
    def edit(self,id=0):
        logging.debug("????? in edit")
        item = Email.get(self.user.site_id,id=id)
        if item == None and (id == None or id == 0):
            item = Email(site_id=self.user.site_id,subject='')
        self.render('email.html',item=item)
    
    @requires_admin
    def testsecurity(self,id=0):
        """This is only for unit tests to ensure we don't have
        access as it requires a non existent role"""
        return 'failed test security'
    

_controllers = [
    (r"/email/(.*?)/(.*?)", EmailController),
    (r"/email/(.*?)", EmailController),
]
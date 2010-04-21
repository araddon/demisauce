import logging
import urllib
from wtforms import Form, BooleanField, TextField, TextAreaField, \
    PasswordField, SelectField, SelectMultipleField, HiddenField, \
    IntegerField, validators
from wtforms.validators import ValidationError
#from sqlalchemy.orm import eagerload
from demisauce.lib import QueryDict
from sqlalchemy.sql import and_, or_, not_, func, select
from demisauce import model
from demisauce.model import meta
from demisauce.model.template import Template
from demisauce.controllers import BaseHandler, RestMixin, SecureController, \
    requires_admin

log = logging.getLogger(__name__)

class TemplateForm(Form):
    def validate_slug(form, field):
        logging.debug("validating slug:  person_id = %s" % (form.id.data))
        e = meta.DBSession.query(Template).filter(and_(
            Template.slug == field.data.lower(),Template.site_id==form.site_id.data)).first()
        if e and e.id != int(form.id.data):
            logging.debug("dupe slug for email: form.id.data:  %s, pid=%s" % (form.id.data,e.id))
            raise ValidationError(u'That slug is already in use, please choose another')
    id              = HiddenField('id',default=0)
    site_id         = HiddenField('site_id',default=0)
    template        = TextField('Template')
    template_html   = TextField('Template_html')
    subject         = TextField('subject')
    slug            = TextField('from_name', [validate_slug])
    from_name      = TextField('from_name')
    from_email      = TextField('from_email')
    to              = TextField('to')

class TemplateController(RestMixin, SecureController):
    requires_auth = True
    
    def index(self,id=0):
        if id > 0:
            items = [meta.DBSession.query(Template).get(id)]
        else:
            items = meta.DBSession.query(Template).filter_by(site_id=self.user.site_id).all()
        self.render('email.html',items=items)
    
    def edit_POST(self,id=0):
        if self.get_argument("id") == "0":
            item = Template(site_id=self.user.site_id, subject=self.get_argument("subject"))
        else:
            id = self.get_argument("id")
            item = meta.DBSession.query(Template).filter_by(id=id,site_id=self.user.site_id).first()
            
        form = TemplateForm(QueryDict(self.request.arguments),item)
        form.site_id.data = self.user.site_id
        form.id.data = self.current_user.id
        if item and form.validate():
            item.subject = form.subject.data
            item.template = form.template.data
            item.template_html = form.template_html.data
            item.from_name = form.from_name.data
            item.from_email = form.from_email.data
            item.slug = self.get_argument('real_permalink')
            item.to = form.to.data
            item.save()
            self.add_alert('updated email template')
            return self.index()
        else:
            return self.render('email.html',form=form,item=item)
    
    def delete(self,id=0):
        item = Template.get(self.user.site_id,id=id)
        if item != None:
            item.delete()
        self.add_alert('deleted email template')
        return self.redirect('/email/index')
    
    def edit(self,id=0):
        logging.debug("????? in edit")
        item = Template.get(self.user.site_id,id=id)
        if item == None and (id == None or id == 0):
            item = Template(site_id=self.user.site_id,subject='')
        self.render('email.html',item=item)
    
    @requires_admin
    def testsecurity(self,id=0):
        """This is only for unit tests to ensure we don't have
        access as it requires a non existent role"""
        return 'failed test security'
    

_controllers = [
    (r"/email/(.*?)/(.*?)", TemplateController),
    (r"/email/(.*?)", TemplateController),
]
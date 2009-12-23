#!/usr/bin/env python
import logging
import urllib
from wtforms import Form, BooleanField, TextField, TextAreaField, \
    PasswordField, SelectField, SelectMultipleField, HiddenField, \
    IntegerField, validators
from wtforms.validators import ValidationError
from demisauce.lib import QueryDict, sanitize
from demisauce.controllers import RestMixin, BaseHandler, requires_admin
from demisauce import model
from demisauce.model import meta
from demisauce.model import mapping
from demisauce.model.person import Person
from demisauce.model.site import Site
from demisauce.model.email import Email

log = logging.getLogger(__name__)

class SiteForm(Form):
    def validate_email(form, field):
        s = meta.DBSession().query(Site).filter(Site.email == field.data).first()
        if s and s.id != int(form.id.data):
            logging.debug("duplicate email in site s.email=%s, field.data=%s" % (s.email,field.data))
            raise ValidationError(u'That Email is already in use, choose another')
    
    def validate_slug(form, field):
        f = meta.DBSession().query(Site).filter(Site.slug == field.data).first()
        if f and f.id != int(form.id.data):
            logging.debug("dupe slug: form.slug.data:  %s, f.id=%s, field.data=%s" % (form.slug.data,f.id,field.data))
            raise ValidationError(u'That slug is already in use, choose another')
    
    email           = TextField('Email', [validators.Email()])
    id              = HiddenField('id',default="0")
    name            = TextField('Name', [validators.length(min=4, max=128)])
    description     = TextAreaField('Description')
    slug            = TextField('slug')
    site_url        = TextField('Site Url')
    base_url        = TextField('Base Url')
    public          = BooleanField('List Public')

class SiteController(RestMixin,BaseHandler):
    
    def index(self,id=0):
        return self.view(self.user.site_id)
    
    def view(self,id = 0):
        id = int(id) if id is not None else 0
        logging.debug("in site view id= %s" % (id))
        if id > 0 and (self.user is not None) and self.user.issysadmin:
            item = Site.saget(id)
        elif (id is None or id == 0) or (self.user and self.user.site_id == id):
            item = Site.get(-1,self.user.site_id)
        else:
            item = Site.get(-1,id)
            if not item.public:
                item = None
        self.render('site/site.html',item=item)
    
    @requires_admin
    def cmntconfig(self):
        item = Site.get(-1,self.user.site_id)
        self.render('/site/comment.html',item=item)
    
    @requires_admin
    def help(self,id = 0):
        if id > 0:
            c.item = Site.get(-1,id)
            c.base_url = config['demisauce.url']
        else:
            c.item = Site.get(-1,self.user.site_id)
        self.render('/help/help.html')
    
    @requires_admin
    def edit(self,id = 0):
        id = int(id)
        if id > 0 and self.user.isadmin and self.user.site_id == id:
            item = meta.DBSession.query(Site).get(id)
        elif id > 0 and self.user.issysadmin:
            item = meta.DBSession.query(Site).get(id)
        form = SiteForm(QueryDict(self.request.arguments),item)
        logging.debug("form.name.data %s" % (form.name.data))
        self.render('/site/site_edit.html',item=item,form=form)
    
    @requires_admin
    #@validate(schema=SiteValidation(), form='edit')
    def edit_POST(self,id = 0):
        """
        User has selected to change site config info
        """
        site = Site.get(-1,self.get_argument('id'))
        form = SiteForm(QueryDict(self.request.arguments))
        if form and site and form.validate():
            
            
            if site is None:
                self.add_error("We experienced an error, please try again")
                
            else:
                site.name = form.name.data
                logging.debug("description pre sanitize = %s" % form.description.data)
                site.description = sanitize.sanitize(form.description.data)
                site.email = form.email.data
                site.slug = self.get_argument('real_permalink')
                # TODO, check uniqueness
                site.public = bool(form.public.data)
                site.base_url = form.base_url.data
                site.site_url = form.site_url.data
                site.save()
                
                # refresh session store
                user = Person.get(self.user.site_id,self.user.id)
                self.set_current_user(user)
                self.add_alert("Site settings were updated")
                
            
        else:
            logging.error(form.errors)
            logging.error("There was an Error site=%s  form.data%s" % (site,form.data))
            self.add_error("There was an Error")
            return self.render('/site/site_edit.html',item=site,form=form)
        return self.redirect('/site/view?msg=Site+Updated')
    


_controllers = [
    (r"/site/(.*?)/(.*?)", SiteController),
    (r"/site/(.*?)", SiteController),
]

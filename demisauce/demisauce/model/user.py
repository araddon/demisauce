import logging
from sqlalchemy import Column, MetaData, ForeignKey, Table, \
    func, UniqueConstraint
from sqlalchemy import Integer, String as DBString, DateTime, Boolean, \
    Text as DBText
from sqlalchemy import engine, orm
from sqlalchemy.sql import and_, text
from datetime import datetime
import formencode
import random, hashlib, string
from wtforms import Form, BooleanField, TextField, TextAreaField, \
    PasswordField, SelectField, SelectMultipleField, HiddenField, \
    IntegerField, validators
from wtforms.validators import ValidationError
from tornado import escape
from tornado.options import options
from demisauce import model
from demisauce.model import meta
from demisauce.model.site import Site
from demisauce.model.activity import Activity
from demisauce.model import ModelBase, JsonMixin
from datetime import datetime

# Person 
person_table = Table("person", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("foreign_id", Integer, default=0, index=True),
        Column("email", DBString(255)),
        Column("displayname", DBString(50)),
        Column("created", DateTime,default=datetime.now),
        Column("last_login", DateTime),
        Column("waitinglist", Integer, default=1),
        Column("verified", Boolean, default=False),
        Column("isadmin", Boolean, default=False),
        Column("issysadmin", Boolean, default=False),
        Column("user_uniqueid", DBString(40)),
        Column("authn", DBString(8),default='local'),
        Column("hashedemail", DBString(32), nullable=True),
        Column("url", DBString(255),default="http://yourapp.wordpress.com",nullable=False),
        Column("random_salt", DBString(120)),
        Column("hashed_password", DBString(120)),
        Column("extra_json", DBText),
        UniqueConstraint('hashedemail','site_id'),
    )

# DB Table:  group ---------------------------
group_table = Table("group", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("author_id", Integer, nullable=True,default=0),
        Column("created", DateTime,default=datetime.now),
        Column("group_type", DBString(30), default='groups'),
        Column("name", DBString(255), nullable=False),
        Column("slug", DBString(150), nullable=False),
        Column("description", DBString(500)),
        Column("contacts", DBText),
        Column("public", Boolean, default=False),
    )
groupperson_table = Table('person_group', meta.metadata,
    Column('group_id', Integer, ForeignKey('group.id')),
    Column('person_id', Integer, ForeignKey('person.id')),
)

class SignupForm(Form):
    def validate_email(form, field):
        f = meta.DBSession().query(Person).filter(Person.email == field.data).first()
        if f:
            logging.debug("f.email=%s, field.data=%s" % (f.email,field.data))
            raise ValidationError(u'That Email is already in use, choose another')
    email           = TextField('Email', [validators.Email()])

class InviteForm(Form):
    password        = PasswordField('New Password')
    password2       = PasswordField('Confirm Password', [validators.Required(), validators.EqualTo('password', message='Passwords must match')])
    displayname     = TextField('Display Name')
    sitename        = TextField('Name of your site')
    
class GroupForm(Form):
    "Form validation for the comment web admin"
    name        = TextField('Name of your Group')
    members        = TextField('list of members')

"""
class ProducerForm(Form):
    def validate_slug(form, field):
        f = model.gsession().query(model.Producer).filter(model.Producer.slug == field.data).first()
        if f and f.id != int(form.id.data):
            logging.debug("form.id.data:  %s, f.id=%s, field.data=%s" % (form.id.data,f.id,field.data))
            raise ValidationError(u'That slug is already in use, choose another')
    password        = PasswordField('New Password')
    password2       = PasswordField('Confirm Password', [validators.Required(), validators.EqualTo('password', message='Passwords must match')])
    id              = HiddenField('id',default="0")
    name            = TextField('Name', [validators.length(min=4, max=128)])
    description     = TextAreaField('Producer Description')
    short_description = TextAreaField('Short Description')
    address         = TextField('Address', [validators.length(min=4, max=256)])
    email           = TextField('Email')
    slug            = TextField('slug')
    website         = TextField('Site Url')
    profile_pic     = TextField('Profile Photo')
    zipcode         = TextField('Zipcode')
    regionzipid     = HiddenField('regionzip_id',default=2)
    geopt_address   = HiddenField('geopt_address')
    accepted_terms  = IntegerField('Accept Terms')
"""
from formencode import Invalid, validators
from formencode.validators import *

class UniqueEmail(formencode.FancyValidator):
    def _to_python(self, value, state):
        #raise formencode.Invalid('Sorry, this is hosed', value, state)
        user = meta.DBSession.query(Person).filter_by(email=value.lower()).first()
        # We can use user[0] because if the user didn't exist this would not be called
        if user:
            raise formencode.Invalid('that email is already registered', value, state)
        return value

class InvitationIsValid(formencode.FancyValidator):
    def _to_python(self, value, state):
        user = meta.DBSession.query(Person).filter_by(
                            user_uniqueid=value.lower()).first()
        if not user:
            raise formencode.Invalid('Invalid Invitation code', value, state)
        return value
    

"""
class GuestValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    email = formencode.All(validators.Email(resolve_domain=False),
                           validators.String(not_empty=True),
                           UniqueEmail())
"""

class InviteValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    #email = formencode.All(validators.Email(resolve_domain=False),
    #                       validators.String(not_empty=True))
    invitecode = formencode.All(InvitationIsValid())
    password = formencode.All(validators.NotEmpty(),validators.MinLength(5))
    password2 = formencode.All(validators.NotEmpty(),validators.MinLength(5))

class PersonValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    email = formencode.All(validators.Email(resolve_domain=False),
                           validators.String(not_empty=True))
    password = formencode.All(validators.NotEmpty(),validators.MinLength(5))

class PersonEditValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    email = formencode.All(validators.Email(resolve_domain=False),
                           validators.String(not_empty=True))
    displayname = formencode.All(validators.String(not_empty=True))

class Person(ModelBase,JsonMixin):
    """User/Person, base identity and user object
    :email: email of user
    :site_id: id of the site the current user belongs to
    :displayname: Full Name (first + last) of user (or whatever they enter)
    :created:  date they joined
    :last_login: date they last logged on
    :hashedemail: md5 hashed email that is Gravatar_ format
    :url:  url to blog or site of user
    :profile_url:  url to json api
    :authn:  local, google, openid, etc (which authN method to use)
    :user_uniqueid: uniqueid of user (random) for use in querystring's instead of id
    :foreign_id:  id (number) of user within your system
    :issysadmin:  is user a sysadmin (admin for all sites)
    :isadmin:   is user an admin for current site
    .. _Gravatar: http://www.gravatar.com/
    """
    __jsonkeys__ = ['email','displayname','url','site_id', 'raw_password','created']
    _allowed_api_keys = ['isadmin','email','displayname','url','raw_password','authn','user_uniqueid','foreign_id','extra_json']
    schema = person_table
    def __init__(self, **kwargs):
        super(Person, self).__init__(**kwargs)
        self.after_load()
        self.init_on_load()
    
    @orm.reconstructor
    def init_on_load(self):
        "called by sq after load as init type"
        self.session = {'testcrap':'crap'}
    
    @property
    def profile_url(self):
        if self.hashedemail:
            return "%s/api/person/%s.json" % (options.base_url,self.hashedemail)
        return "%s/api/person/%s.json" % (options.base_url,self.id)
    
    def isvalid(self):
        'after user data has been loaded in, ensures is valid'
        #what to check?  email has been validated by get?
        return True
    
    def after_load(self):
        self.create_user_salt()
        self.user_uniqueid = Person.create_userunique()
        if self.email != None:
            self.set_email(self.email)
            self.hashedemail = Person.create_hashed_email(self.email)
        if not hasattr(self,'displayname') and self.email != None:
            self.displayname = self.email
        if hasattr(self,'raw_password'): 
             self.set_password(self.raw_password)
    
    def create_password(self, size=7):
        """
        Generates a password and returns it
        """
        import string
        from random import choice
        return ''.join([choice(string.letters + string.digits) for i in range(size)])
    
    @classmethod
    def create_userunique(self):
        """
        classmethod, Creates a random set of characters for user unique 
        "code", use as a guid type thing in querystring's
        
        returns the value of user_unquieid
        """
        return hashlib.md5(str(random.random())).hexdigest()
    
    @classmethod
    def create_random_email(cls,domain='@demisauce.org'):
        """
        create a random email for testing
        accepts a @demisauce.org domain argument optionally
        """
        return '%s%s' % (hashlib.md5(str(random.random())).hexdigest(),
            domain)
    
    @classmethod
    def create_hashed_email(self,email):
        """
        Classmethod to accept an email and hash it into md5 hash
        that is a Gravatar_  email
        
        returns hashed email
        
        .. _Gravatar: http://www.gravatar.com/
        """
        return hashlib.md5(email.lower()).hexdigest()
    
    def set_email(self,email):
        self.email = email.lower()
        self.hashedemail = hashlib.md5(email.lower()).hexdigest()
    
    def create_user_salt(self):
        """
        creates random salt
        """
        self.random_salt = hashlib.md5(str(random.random())).hexdigest()[:15]
    
    def set_password(self, raw_password):
        if self.random_salt == None or len(self.random_salt) < 5:
            self.create_user_salt()
        self.hashed_password = hashlib.sha1(self.random_salt+raw_password).hexdigest()
    
    def is_authenticated(self, supplied_pwd):
        """
        Returns a boolean of whether the supplied password was correct.
        """
        if self.random_salt == None: return False
        return (self.hashed_password == hashlib.sha1(self.random_salt+supplied_pwd).hexdigest())
    
    def public_token(self):
        """create's a token for user """
        return hashlib.md5(self.random_salt+str(self.id)).hexdigest()
    
    def help_tickets(self,ct=10):
        """Returns list of help tickets i have submited"""
        from demisauce.model.help import Help
        return meta.DBSession.query(Help).filter_by(
                site_id=self.site_id, hashedemail=self.hashedemail
                ).order_by(Help.created.desc()).limit(ct)
    
    def recent_comments(self,ct=5):
        """Returns recent comments"""
        from demisauce.model.help import Help
        return meta.DBSession.query(model.comment.Comment).filter_by(
                site_id=self.site_id, hashedemail=self.hashedemail
                ).order_by(model.comment.Comment.created.desc()).limit(ct)
    
    def get_recent_activities(self,ct=5):
        return self.activities.order_by(Activity.created.desc()).limit(ct)
    recent_activities = property(get_recent_activities)
    
    # =====  Serialization
    def to_dict_basic(self):
        "Basic User info to dict"
        return self.to_dict(keys=['id','displayname','email','user_uniqueid'])
    
    def to_json(self,keys=None):
        output = self.to_dict(keys=keys)
        if hasattr(self,'attributes'):
            attributes = []
            for attr in self.attributes:
                attributes.append(attr.to_dict())
            output['attributes'] = attributes
        output['session'] = self.session
        return escape.json_encode(output)
    
    def from_json(self,json_string):
        """
        Chainable - Converts from a json string back to a populated object::
            
            peep = Person().from_json(json_string)
        
        """
        json_dict = escape.json_decode(json_string)
        self.from_dict(json_dict)
        if 'attributes' in json_dict:
            for attribute in json_dict['attributes']:
                self.attributes.append(PersonAttribute().from_dict(attribute))
        if 'session' in json_dict:
            self.session = json_dict['session']
        
        return self
    
    def __str__(self):
        return "{person:{site_id:%s, id:%s, email:%s}}" % (self.site_id,self.id,self.email)
    
    def has_role(self,role):
        """returns true/false if a user has a specific role
        or accepts a list of roles and if user has any of those roles"""
        roles = []
        if self.isadmin:
            roles.append('admin')
        if self.issysadmin:
            roles.append('sysadmin')
        if type(role) == list:
            for r in role:
                if r in roles:
                    return True
        else:
            if role in roles:
                return True
        return False
    
    def delete(self):
        res = meta.engine.execute(text("delete from activity where person_id=%s" % self.id))
        res = meta.engine.execute(text("delete from person_group where person_id=%s" % self.id))
        res = meta.engine.execute(text("delete from person where id = %s" % self.id))
    
    @classmethod
    def by_site(cls,site_id=0):
        """
        Gets list of all persons for a site (could be large)
        """
        return meta.DBSession.query(Person).filter_by(site_id=site_id).all()
    
    @classmethod
    def by_unique(self,user_unique=''):
        """Get the user by Unique ID"""
        return meta.DBSession.query(Person).filter_by(user_uniqueid=user_unique).first()
    
    @classmethod
    def by_hashedemail(self,site_id=0,hash=''):
        """Get the user by hashed email"""
        return meta.DBSession.query(Person).filter_by(site_id=site_id,hashedemail=hash).first()
    
    @classmethod
    def by_email(self,site_id=0,email=''):
        """Get the user by email"""
        return meta.DBSession.query(Person).filter_by(site_id=site_id,email=email.lower()).first()
    
    @classmethod
    def by_foreignid(self,site_id=0,id=0):
        """Get the user by foreignid"""
        return meta.DBSession.query(Person).filter_by(site_id=site_id,foreign_id=id).first()
    
    
    @classmethod
    def by_email(self,site_id=0,email=''):
        """Get the user by hashed email"""
        return meta.DBSession.query(Person).filter_by(site_id=site_id,email=email).first()
    

class Group(ModelBase,JsonMixin):
    """Groups of users
    :name: name of this group
    :email_list: comma delimited list of email address's of this group
    :members: List of person objects
    :created:  date created
    :description: description
    """
    def __init__(self,site_id=0, name='', description=""):
        super(Group, self).__init__(**kwargs)
        self.init_on_load()
    
    @orm.reconstructor
    def init_on_load(self):
        "called by sq after load as init type"
        pass
    
    def save(self):
        if ((not hasattr(self,'slug')) or self.slug == None) and self.name != None:
            self.slug = self.makekey(self.name)
        super(Group, self).save()
    
    def get_email_list(self):
         return ', '.join(['%s' % m.email.strip(string.whitespace).lower() for m in self.members])
    email_list = property(get_email_list)
    
    def add_memberlist(self,member_list):
        """
        Accepts a comma delimited list of contacts
        returns a tuple of lists, first of new users not already in this group
        2nd of users newly added to system
        """
        #ml = [m.strip(string.whitespace) for m in member_list.replace(';',',').split(',') if len(m) > 4]
        ml_temp = member_list.replace(';',',').lower()
        cl = [ e.strip(string.whitespace) for e in ml_temp.split(',') if len(e) > 5]
        
        ml = ['%s' % m.email.strip(string.whitespace).lower() for m in self.members]
        
        newlist = [e for e in cl if not ml.__contains__(e.strip(string.whitespace))]
        
        removelist = [e for e in ml if not cl.__contains__(e.strip())]
        [self.remove_member(e) for e in removelist]
        addedusers = [self.add_member(e) for e in newlist]
        newtosite = [e for e in addedusers if e != None]
        newtogroup = [e for e in newlist if not addedusers.__contains__(e)]
        #self.contacts = ','.join(self.__members)
        return newtogroup, newtosite  
    
    def remove_member(self, newemail):
        """
        removes a user
        """
        [self.members.remove(p) for p in self.members if p.email.lower() == newemail]
    
    def member_byemail(self, email):
        """
        returns a user from members list that has given email?
        """
        for p in self.members:
            if p.email.lower() == email:
                return p
        
        return None
    
    def add_member(self, newemail):
        # don't trust this user is new
        p = Person.by_email(self.site_id,newemail)
        if p and p.id > 0:
            self.members.append(p)
        else:
            self.members.append(Person(site_id=self.site_id,email=newemail))
            return newemail
    
    @classmethod
    def by_site(cls,site_id=0,ct=15,filter='new'):
        """Class method to get groups"""
        return meta.DBSession.query(Group).filter_by(
            site_id=site_id).order_by(group_table.c.created.desc()) #.limit(ct)
        
    
    @classmethod
    def by_slug(cls,site_id=0,slug=''):
        """
        Gets the group by slug for a site::
            
            Group.by_slug(c.site_id,'all-users')
        """
        return meta.DBSession.query(Group).filter_by(site_id=site_id,slug=slug).first()
    
   
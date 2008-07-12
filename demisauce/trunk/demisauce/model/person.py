from pylons import config
from sqlalchemy import Column, MetaData, ForeignKey, Table, \
    func, UniqueConstraint
from sqlalchemy.types import Integer, String as DBString, DateTime, Boolean
from sqlalchemy.sql import and_
from datetime import datetime
import formencode
import sha, random, hashlib, string
from formencode import Invalid, validators
from formencode.validators import *

from demisauce import model
from demisauce.model import meta
from demisauce.model.site import Site
from demisauce.model.activity import Activity
from demisauce.model import ModelBase
from datetime import datetime

# Person 
person_table = Table("person", meta.metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer, ForeignKey('site.id')),
        Column("email", DBString(255)),
        Column("displayname", DBString(50)),
        Column("created", DateTime,default=datetime.now()),
        Column("last_login", DateTime),
        Column("waitinglist", Integer, nullable=False,default=1),
        Column("verified", Boolean, default=False),
        Column("isadmin", Boolean, default=False),
        Column("issysadmin", Boolean, default=False),
        Column("user_uniqueid", DBString(40)),
        Column("authn", DBString(8),default='local'),
        Column("hashedemail", DBString(32), nullable=True),
        Column("url", DBString(255),default="http://yourapp.wordpress.com",nullable=False),
        Column("random_salt", DBString(120)),
        Column("hashed_password", DBString(120)),
        UniqueConstraint('email','site_id'),
    )

class InvitationIsValid(formencode.FancyValidator):
    def _to_python(self, value, state):
        user = meta.DBSession.query(Person).filter_by(
                            user_uniqueid=value.lower()).first()
        if not user:
            raise formencode.Invalid('Invalid Invitation code', value, state)
        return value
    

class UniqueEmail(formencode.FancyValidator):
    def _to_python(self, value, state):
        #raise formencode.Invalid('Sorry, this is hosed', value, state)
        user = meta.DBSession.query(Person).filter_by(email=value.lower()).first()
        # We can use user[0] because if the user didn't exist this would not be called
        if user:
            raise formencode.Invalid('that email is already registered', value, state)
        return value
    

class GuestValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    email = formencode.All(validators.Email(resolve_domain=False),
                           validators.String(not_empty=True),
                           UniqueEmail())
    

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

class Person(object,ModelBase):
    """
    User/Person, base identity and user object
    
    :email: email of user
    :site_id: id of the site the current user belongs to
    :displayname: Full Name (first + last) of user (or whatever they enter)
    :created:  date they joined
    :last_login: date they last logged on
    :hashedemail: md5 hashed email that is Gravatar_ format
    :url:  url to blog or site of user
    :authn:  local, google, openid, etc (which authN method to use)
    :user_uniqueid: uniqueid of user (random) for use in querystring's instead of id
    
    .. _Gravatar: http://www.gravatar.com/
    """
    __jsonkeys__ = ['email','displayname','url','site_id', 'raw_password','created']
    def __init__(self, site_id, email, displayname=None, raw_password=None):
        self.site_id = site_id
        self.set_email(email)
        self.displayname = displayname
        if displayname == None:
            self.displayname = email
        self.create_user_salt()
        self.user_uniqueid = Person.create_userunique()
        if raw_password != None: 
            self.set_password(raw_password)
        self.hashedemail = Person.create_hashed_email(email)
        self.raw_password = raw_password # note, this doesn't persist to db, temp
    
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
        return sha.new(str(random.random())).hexdigest()
    
    @classmethod
    def create_random_email(cls,domain='@demisauce.org'):
        """
        create a random email for testing
        accepts a @demisauce.org domain argument optionally
        """
        return '%s%s' % (sha.new(str(random.random())).hexdigest(),
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
        import hashlib
        self.email = email.lower()
        self.hashedemail = hashlib.md5(email.lower()).hexdigest()
    
    def create_user_salt(self):
        """
        creates random salt
        """
        import sha, random
        self.random_salt = sha.new(str(random.random())).hexdigest()[:15]
    
    def set_password(self, raw_password):
        import sha, random
        if self.random_salt == None or len(self.random_salt) < 5:
            self.create_user_salt()
        self.hashed_password = sha.new(self.random_salt+raw_password).hexdigest()
    
    def is_authenticated(self, supplied_pwd):
        """
        Returns a boolean of whether the supplied password was correct.
        """
        import sha
        if self.random_salt == None: return False
        return (self.hashed_password == sha.new(self.random_salt+supplied_pwd).hexdigest())
    
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
                ).order_by(model.comment.Comment.created.desc()).all()
    
    
    def get_recent_activities(self,ct=5):
        return self.activities.order_by(Activity.created.desc()).limit(ct)
    recent_activities = property(get_recent_activities)
    
    def to_json(self,indents=2):
        """converts to json string, converting non serializeable fields
        to some other format or ignoring them"""
        d = self.__dict__#.copy()
        # cs = time.mktime(self.created.timetuple()) # convert to seconds
        # to get back:  datetime.datetime.fromtimestamp(cs)
        import time, simplejson, datetime
        dout = {}
        
        for key in self.__class__.__jsonkeys__:
            if type(self.__dict__[key]) == datetime.datetime:
                dout.update({key:time.mktime(self.__dict__[key].timetuple())})
            else:
                dout.update({key:self.__dict__[key]})
        
        return simplejson.dumps(dout,indent=indents)
    
    def __str__(self):
        return "id=%s, email=%s" % (self.id,self.email)
    
    @classmethod
    def get_by_sitexx(cls,site_id=0,id=0):
        """
        Class method to get person by, similar to Person.get()
        except it ensures in the same site as user for 
        in case they are munging with querystring etc.
        
        site_id
            the id of site of current user
        
        id
            id# of the person to get
        """
        return meta.DBSession.query(Person).filter_by(site_id=site_id,id=id).first()
    
    @classmethod
    def by_site(cls,site_id=0):
        """
        Gets list of all persons for a site (could be large)
        """
        return meta.DBSession.query(Person).filter_by(site_id=site_id).all()
    
    @classmethod
    def by_hashedemail(self,site_id=0,hash=''):
        """Get the user by hashed email"""
        return meta.DBSession.query(Person).filter_by(site_id=site_id,hashedemail=hash).first()
    
    @classmethod
    def by_email(self,site_id=0,email=''):
        """Get the user by hashed email"""
        return meta.DBSession.query(Person).filter_by(site_id=site_id,email=email).first()
    

        
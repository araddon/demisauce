import logging
from tornado.options import options
import tornado.escape
from demisauce.lib.base import *
from datetime import datetime, timedelta
import demisauce.model
from demisauce.model.site import *
from demisauce.model.activity import Activity
from demisauce.model.person import Person, PersonValidation, \
    GuestValidation, PersonEditValidation, InviteValidation
from demisauce.model.comment import Comment
from demisauce.model.activity import Activity, add_activity
from formencode import Invalid, validators
from formencode.validators import *
import formencode, urllib
import demisaucepy.cache_setup
from demisaucepy.cache import cache
from demisauce.controllers import BaseHandler, RestMixin, SecureController

log = logging.getLogger(__name__)

def google_auth_url(return_url):
    import urllib
    from gdata import auth
    url = urllib.urlencode({'url':return_url})
    next = '%s/account/googleauth?%s' % (options.base_url,url)
    scope = 'http://www.google.com/m8/feeds'
    auth_sub_url = auth.GenerateAuthSubUrl(next,scope,secure=False,session=True)
    return auth_sub_url

def compute_userhash():
    if 'HTTP_USER_AGENT' in request.environ and 'REMOTE_ADDR' in request.environ:
        hash = request.environ['HTTP_USER_AGENT'] + request.environ['REMOTE_ADDR'] 
        import hashlib
        return hashlib.md5(hash + config['demisauce.apikey']).hexdigest()
    else:
        return None

class PasswordChangeValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    password = formencode.All(validators.NotEmpty())
    password1 = formencode.All(validators.NotEmpty(),validators.MinLength(5))
    password2 = formencode.All(validators.NotEmpty(),validators.MinLength(5))
    chained_validators = [validators.FieldsMatch('password1', 'password2')]
    

class AccountController(RestMixin,BaseHandler):
    requires_auth = False

    def googleauth(self):
        """
        User is coming in from google, should have an auth token
        """
        # NEED SITE????  Or does that not make sense?
        import gdata
        import gdata.contacts
        import gdata.contacts.service
        authsub_token = self.get_argument("token")
        log.info('calling gdata_authsubtoke = %s' % (authsub_token))
        #TODO:  upgrade to gdata 1.2+ which breaks this
        gd_client = gdata.contacts.service.ContactsService()
        gd_client.auth_token = authsub_token
        gd_client.UpgradeToSessionToken()
        query = gdata.contacts.service.ContactsQuery()
        query.max_results = 2
        feed = gd_client.GetContactsFeed(query.ToUri())
        email = feed.author[0].email.text
        name = feed.author[0].name.text
        user = meta.DBSession.query(Person).filter_by(
                    email=email.lower()).first()
        if not user:
            user = Person(site_id=1,email=email,displayname=name)
            user.authn = 'google'
            user.save()
            log.info('creating a google user')
        self.set_current_user(user,is_authenticated = True,islogon=True)
        expires_seconds = 60*60*24*31
        self.set_cookie('userkey', user.user_uniqueid,expires_days=31)
        if 'url' in self.request.arguments:
            url = request.GET['url']
            self.redirect(str(url))
        self.render('/comment/comment_login.html')
    
    
    #@rest.dispatch_on(POST="update_account")
    def index(self):
        if not self.user:
            return self.redirect('/account/signin')
        self.render('/account/settings.html')
    
    #@rest.dispatch_on(POST="inviteusers_POST")
    def inviteusers(self,id=0):
        self.render('/account/inviteusers.html')
    
    def inviteusers_POST(self):
        """
        admin is sending out a number of invites to users
        """
        if 'emails' in self.request.arguments:
            emails = self.request.arguments['emails']
            delay = 4
            from demisauce.lib import scheduler
            for email in emails.split(','):
                email = email.strip().lower()
                user = Person.by_email(self.user.site_id,email)
                
                if user is None:
                    user = Person(site_id=c.site_id,email=email, displayname=email)
                    user.save()
                    #send emails
                    url2 = urllib.quote_plus('/account/viewh/%s' % (user.hashedemail))
                    dnew = {}
                    dnew['link'] = '%s/account/verify?unique=%s&node=%s&return_url=%s' %\
                        (base_url(),user.user_uniqueid,user.id,url2)
                    dnew['from'] = self.user.displayname
                    a = Activity(site_id=user.site_id,person_id=user.id,activity='sending email invite')
                    a.ref_url = 'account admin invite'
                    a.category = 'account'
                    a.save()
                    scheduler.add_interval_task(send_emails,0,('invitation_to_demisauce',[user.email],dnew) , initialdelay=delay)
                    delay += 3
                
            return 'from form %s' % emails
        return 'error'
    
    #@rest.dispatch_on(POST="signup_POST")
    def signup(self):
        user = self.get_current_user()
        if user:
            self.add_alert('Already signed in.')
            #redirect_wsave(action='index')
        
        self.render('/account/signup.html')
    
    #@rest.dispatch_on(POST="site_signup_POST")
    def site_signup(self,id=''):
        if self.user:
            h.add_alert('Already signed in.')
            #redirect_wsave(action='index')
        elif 'invitecode' in request.params:
            session.clear()
            self.user = meta.DBSession.query(Person).filter_by(
                        user_uniqueid=request.params['invitecode']).first()
            c.invitecode = request.params['invitecode']
        self.render('/account/sitesignup.html')
    
    #@validate(schema=InviteValidation(), form='site_signup')
    def site_signup_POST(self):
        """
        User is signing up
        """
        user = meta.DBSession.query(Person).filter_by(
                    user_uniqueid=self.form_result['invitecode'].lower()).first()
        if user is None:
            h.add_error("We were not able to verify this invite, please \
                try again or enter your email in the top form for the waiting list.")
        else:
            user.set_password(self.form_result['password'])
            user.site.name = self.form_result['sitename']
            user.displayname = self.form_result['displayname']
            user.verified = True
            user.isadmin = True
            model.setup_site(user)
            self.start_session(user)
            user.save()
            h.add_alert('Account was created')
            
            return self.returnurl_orgoto(controller='home',action='index')
            
        self.render('/account/signup.html')
    
    #@rest.dispatch_on(POST="verify_POST")
    def verify(self):
        if self.user:
            #h.add_alert('Already signed in.')
            redirect_wsave(controller='home',action='index')
        
        # destination included?
        if 'return_url' in request.params:
            # Remember where we came from so that the user can be sent there
            # after a successful login
            session['return_url'] = request.params['return_url']
            session.save()
                
        if 'unique' in request.params:
            user = meta.DBSession.query(Person).filter_by(
                    user_uniqueid=request.params['unique'].lower()).first()
            # TODO should we validate a time stamp?
            
            if user is None:
                h.add_error("That link does not appear to be valid,\
                    please contact the person that invited you or sign up.")
                
                return redirect_wsave("/account/signup" )
                return self.signup()
            elif user.verified == True:
                # this user already registered
                h.add_alert('Already verified account')
                return redirect_wsave("/account/signin" )
            else:
                self.user = user
        self.render('/account/verify.html')
    
    #@validate(schema=PersonValidation(), form='verify')
    def verify_POST(self):
        """
        User has selected to enter a username pwd
        This is a "mini" form, signup is full one
        """
        if 'unique' in request.params:
            user = meta.DBSession.query(Person).filter_by(
                    user_uniqueid=request.params['unique'].lower()).first()
            # TODO should we validate a time stamp?
            
            if user is None:
                h.add_error("We were not able to verify this invite, please try again")
                
            elif 'password' in self.form_result:
                user.displayname = self.form_result['displayname']
                user.set_password(self.form_result['password'])
                user.verified = True
                user.waitinglist = False
                response.set_cookie('userkey', user.user_uniqueid,
                                expires=datetime.today() + timedelta(days=31))
                self.start_session(user)
                user.save()
                
            else:
                h.add_error("You did not submit a password, please try again.")
            
            return self.returnurl_orgoto(controller='home',action='index')
        
        else:
            h.add_error("You need to enter an email and password to signin.")
        
        self.render('/account/signin.html')
    
    def verifycontinue(self):
        if 'unique' in request.params:
            user = meta.DBSession.query(Person).filter_by(
                    user_uniqueid=request.params['unique'].lower()).first()
            # TODO should we validate a time stamp?
            
            if user is None:
                h.add_error("Whoops, there was an error, please click on the \
                    link in the email again.")
                return self.verify()
            
            else:
                self.start_session(user)
        
        return self.returnurl_orgoto(controller='home',action='index')
    
    #@validate(schema=GuestValidation(), form='signup')
    def interest(self):
        """
        User has selected to enter an email to be on waitinglist
        """
        if 'email' in self.request.arguments:
            user = meta.DBSession.query(Person).filter_by(
                    email=self.request.arguments['email'].lower()).first()
            
            if user is None:
                site = Site(name=self.form_result['email'],email=self.form_result['email'])
                site.save()
                user = Person(site_id=site.id,email=self.form_result['email'],
                              displayname=self.form_result['email'])
                user.slug = user.hashedemail
                user.save()
                a = Activity(site_id=user.site_id,person_id=user.id,activity='Signup Interest Form')
                #a.ref_url = 'comment url'
                a.category = 'account'
                a.save()
                #TODO:  refactor/extract email send to trigger event api
                #send emails
                url2 = urllib.quote_plus('/account/viewh/%s' % (user.hashedemail))
                delay = 4
                from demisauce.lib import scheduler
                dnew = {}
                dnew['link'] = '%s/account/verify?unique=%s&node=%s&return_url=%s' %\
                    (c.base_url,user.user_uniqueid,user.id,url2)
                dnew['displayname'] = user.displayname
                dnew['email'] = user.email
                dnew['title'] = 'welcome'
                scheduler.add_interval_task(send_emails,0,('thank_you_for_registering_with_demisauce',
                    [user.email],dnew) , initialdelay=delay)
                if 'demisauce.admin' in config:
                    scheduler.add_interval_task(send_emails,0,('a-new-user-has-registered',
                        [config['demisauce.admin']],dnew) , initialdelay=8)
            
            h.add_alert("Thank You!")
            return redirect_wsave(controller='home',action='index')
        
        else:
            h.add_error("You need to enter an email.")
        
        self.render('/account/signup.html')
    
    #@rest.dispatch_on(POST="signin_POST")
    def signin(self):
        log.info('made it to account signin?' )
        email = None
        if self.get_current_user():
            return self.redirect("/home/index")
        elif 'userkey' in self.cookies:
            user = meta.DBSession.query(Person).filter_by(
                    user_uniqueid=self.get_cookie('userkey').lower()).first()
            
            if user:
                a = Activity(site_id=user.site_id,person_id=user.id,activity='Logging In')
                #a.ref_url = 'comment url'
                a.category = 'account'
                self.set_current_user(user)
                return self.redirect('/home/default')
        
        if 'email' in self.cookies:
            email = self.get_cookie('email').lower()
                            
        googleurl = google_auth_url('%s/account/usersettings' % options.base_url)
        self.render('/account/signin.html',google_auth_url=googleurl,email=email)
    
    def signin_POST(self):
        log.info('made it to account signin_POST?' )
        if 'email' in self.request.arguments:
            user = meta.DBSession.query(Person).filter_by(
                        email=self.get_argument('email').lower()).first()
            
            if user is None:
                h.add_error("We were not able to verify that email\
                     or password, please try again")
            
            elif 'password' in self.request.arguments:
                if user.is_authenticated(self.get_argument('password')):
                    a = Activity(site_id=user.site_id,person_id=user.id,activity='Logging In')
                    #a.ref_url = 'comment url'
                    a.category = 'account'
                    a.save()
                    remember_me = False
                    if 'remember_me' in self.request.arguments:
                        remember_me = True
                    self.set_current_user(user,is_authenticated = True,remember_me=remember_me,islogon=True)
                    return self.redirect("/dashboard")
                else:
                    h.add_error("We were not able to verify that \
                        email or password, please try again")
            else:
                h.add_error("You did not submit a password, please try again.")
        else:
            h.add_error("You need to enter an email and password to signin.")
            
        self.render('/account/signin.html')
    
    def logout(self):
        if not self.user:
             self.redirect("/")
        self.clear_cookie('userkey')
        self.clear_cookie('user')
        self.redirect("/")
    
    def handshake(self):
        if 'token' in request.params and 'site_slug' in request.params:
            # start a handshake, to figure out if we know this user.
            site = Site.by_slug(str(request.params['site_slug']))
            if site and site.id > 0:
                # lookup user?  how?  
                expire_seconds = 60*60*24*31
                #TODO:  verify that url it came from is in site config
                response.set_cookie('dsu', user.public_token(),path='/',
                        expires=expire_seconds, secure=False)
            return ''
        elif 'usertoken' in request.params:
            pass
            
        """
        if apiuser == None and 'token' in request.params:
            url = 'http://%s/%s?' % (request.environ['HTTP_HOST'],request.environ['PATH_INFO'])
            return_url = urllib.urlencode({'return_url':url})
            url = '%s?token_response=%s&%s' % ('http://demisauce.test:8001/handshake/initial',request.params['token'],return_url)
            #urllib.urlencode({'return_url':'http://localhost:4951/account/handshake'})
            print 'redirecting for handshake url=%s' % url
            # http://demisauce.test:8001/handshake/initial?return_url=http%3A%2F%2Flocalhost%3A4951%2Faccount%2Fhandshake&token=yourtoken
            #redirect_to('http://demisauce.test:8001/handshake/initial?return_url=http%3A%2F%2Flocalhost%3A4951%2Faccount%2Fhandshake&token=%s' % apiuser.hashed_email)
            return redirect_to(url)
        """
    
    #@rest.dispatch_on(POST="account_edit")
    def edit(self):
        if not self.user:
             redirect_to(controller='home', action='index', id=None)
        else:
            c.person = meta.DBSession.query(Person).filter_by(
                    site_id=self.user.site_id, id=self.user.id).first()
        self.render('/account/edit.html')
    
    #@validate(schema=PersonEditValidation(), form='edit')
    def account_edit(self):
        """
        User has selected to update profile
        """
        if self.user and 'email' in self.request.arguments:
            user = Person.get(self.user.site_id,self.user.id)
            user.displayname = self.request.arguments['displayname']
            user.set_email(self.request.arguments['email'])
            user.url = self.request.arguments['url']
            self.start_session(user)
            user.save()
            c.person = user
            self.user = user
            self.start_session(user)
        self.render('/account/settings.html')
    
    #@validate(schema=PasswordChangeValidation(), form='edit')
    def change_pwd(self):
        if self.user:
            user = meta.DBSession.query(Person).filter_by(
                            email=self.user.email.lower()).first()
            c.person = user
            if user.is_authenticated(self.form_result['password']):
                #a = Activity(site_id=user.site_id,person_id=user.id,activity='Changing Password',category='account')
                #a.save()
                add_activity(user,activity='Changing Password',category='account')
                user.set_password(self.form_result['password1'])
                user.save()
                h.add_alert("Your Password was updated")
            else:
                h.add_error("We were not able to verify the \
                    existing password, please try again")
        self.render('/account/settings.html')
    
    def usersettings(self):
        if not self.user:
             redirect_to(controller='home', action='index', id=None)
        else:
            person = meta.DBSession.query(Person).filter_by(
                site_id=self.user.site_id, id=self.user.id).first()
            return self._view(person,getcomments=True)
    
    def _view(self,person,getcomments=False):
        if person:
            helptickets = person.help_tickets()
            activities_by_day = Activity.stats_by_person(person.site_id,person.id)
            activity_count = len(activities_by_day)
            if self.user is None:
                pass
            elif self.user is not None and self.user.issysadmin:
                pass
            elif self.user is not None and self.user.isadmin:
                pass
            else:
                if self.user.site_id == person.site_id:
                    pass
                else:
                    person = None
        else:
            pass #TODO:  raise error, or bad page
        self.render('/account/settings.html',person=person,helptickets=helptickets,
            activities_by_day=activities_by_day,activity_count=activity_count)
    
    def viewh(self,id='blah'):
        person = meta.DBSession.query(Person).filter_by(
            hashedemail=id).first()
        return self._view(person,True)
    
    def view(self,id=0):
        if not self.user:
            redirect_to(controller='home', action='index', id=None)
        
        if self.user.issysadmin and id > 0:
            person = Person.get(-1,id)
        elif id > 0: 
            person = Person.get(self.user.site_id,id)
        
        return self._view(person,True)
    
    def view_mini(self,id=0):
        c.person = None
        if id > 0: # authenticated user
            person = Person.get(self.user.site_id,id)
            c.person = person
        self.render('/account/profile_mini.html')
    
    def pre_init_user(self):
        'a push from app to say we are about to get this user and its good'
        user_key = request.params['user_key']
        site_slug = request.params['site_slug']
        cache.set(user_key,site_slug)
        return ''
    
    def init_user(self,user_key=None):
        # Need site?   
        site_slug = cache.get(user_key)
        if site_slug:
            site = Site.by_slug(site_slug)
            user = meta.DBSession.query(Person).filter_by(
                site_id=site.id, hashedemail=user_key).first()
            self.start_session(user)
            return "success"
    

#map.connect('user/{action}/{id}', controller='account')
#map.connect('{controller}/{action}/{id}')
_controllers = [
    (r"/user/(.*?)/(.*?)/", AccountController),
    (r"/account/(.*?)", AccountController),
]
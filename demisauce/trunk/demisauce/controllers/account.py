import logging
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

log = logging.getLogger(__name__)

class PasswordChangeValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    password = formencode.All(validators.NotEmpty())
    password1 = formencode.All(validators.NotEmpty(),validators.MinLength(5))
    password2 = formencode.All(validators.NotEmpty(),validators.MinLength(5))
    chained_validators = [validators.FieldsMatch('password1', 'password2')]
    

class AccountController(BaseController):
    requires_auth = False
    
    def returnurl_orgoto(self,*args, **kwargs):
        """
        Redirects to url they came in on, else to page specified
        """
        if 'return_url' in session:
            url = session['return_url']
            del(session['return_url'])
            session.save()
            return redirect_wsave(str(url) + '?return_url')
        else:
            return redirect_wsave(*args,**kwargs)
    
    @rest.dispatch_on(POST="update_account")
    def index(self):
        if not c.user:
            redirect_wsave(action='signin')
        return render('/account/settings.html')
    
    @rest.dispatch_on(POST="inviteusers_POST")
    def inviteusers(self,id=0):
        return render('/account/inviteusers.html')
    
    def inviteusers_POST(self):
        """
        admin is sending out a number of invites to users
        """
        if 'emails' in request.POST:
            emails = request.POST['emails']
            delay = 4
            from demisauce.lib import scheduler
            for email in emails.split(','):
                email = email.strip().lower()
                user = Person.by_email(c.user.site_id,email)
                
                if user is None:
                    user = Person(site_id=c.site_id,email=email, displayname=email)
                    user.save()
                    #send emails
                    url2 = urllib.quote_plus('/account/viewh/%s' % (user.hashedemail))
                    dnew = {}
                    dnew['link'] = '%s/account/verify?unique=%s&node=%s&return_url=%s' %\
                        (base_url(),user.user_uniqueid,user.id,url2)
                    dnew['from'] = c.user.displayname
                    a = Activity(site_id=user.site_id,person_id=user.id,activity='sending email invite')
                    a.ref_url = 'account admin invite'
                    a.category = 'account'
                    a.save()
                    scheduler.add_interval_task(send_emails,0,('invitation_to_demisauce',[user.email],dnew) , initialdelay=delay)
                    delay += 3
                
            return 'from form %s' % emails
        return 'error'
    
    @rest.dispatch_on(POST="signup_POST")
    def signup(self):
        if c.user:
            h.add_alert('Already signed in.')
            #redirect_wsave(action='index')
        else:
            session.clear()
        
        return render('/account/signup.html')
    
    @rest.dispatch_on(POST="site_signup_POST")
    def site_signup(self,id=''):
        if c.user:
            h.add_alert('Already signed in.')
            #redirect_wsave(action='index')
        elif 'invitecode' in request.params:
            session.clear()
            c.user = meta.DBSession.query(Person).filter_by(
                        user_uniqueid=request.params['invitecode']).first()
            c.invitecode = request.params['invitecode']
        return render('/account/sitesignup.html')
    
    @validate(schema=InviteValidation(), form='site_signup')
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
            
        return render('/account/signup.html')
    
    @rest.dispatch_on(POST="verify_POST")
    def verify(self):
        if c.user:
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
                c.user = user
        return render('/account/verify.html')
    
    @validate(schema=PersonValidation(), form='verify')
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
        
        return render('/account/signin.html')
    
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
    
    @validate(schema=GuestValidation(), form='signup')
    def interest(self):
        """
        User has selected to enter an email to be on waitinglist
        """
        if 'email' in request.POST:
            user = meta.DBSession.query(Person).filter_by(
                    email=request.POST['email'].lower()).first()
            
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
        
        return render('/account/signup.html')
    
    @rest.dispatch_on(POST="signin_POST")
    def signin(self):
        log.info('made it to account signin?' )
        if c.user:
            redirect_to(controller="home", action='index')
        elif 'userkey' in request.cookies:
            user = meta.DBSession.query(Person).filter_by(
                    user_uniqueid=request.cookies['userkey'].lower()).first()
            
            if not user is None:
                a = Activity(site_id=user.site_id,person_id=user.id,activity='Logging In')
                #a.ref_url = 'comment url'
                a.category = 'account'
                self.start_session(user)
                return self.returnurl_orgoto(controller='home',action='index')
        
        if 'email' in request.cookies:
            c.email = request.cookies['email'].lower()
                            
        session.clear()
        from demisauce.controllers.comment import google_auth_url
        c.google_auth_url = google_auth_url('%s/account/settings' % config['demisauce.url'])
        return render('/account/signin.html')
    
    def signin_POST(self):
        
        if 'email' in request.POST:
            user = meta.DBSession.query(Person).filter_by(
                        email=request.POST['email'].lower()).first()
            
            if user is None:
                h.add_error("We were not able to verify that email\
                     or password, please try again")
            
            elif 'password' in request.POST:
                if user.is_authenticated(request.POST['password']):
                    a = Activity(site_id=user.site_id,person_id=user.id,activity='Logging In')
                    #a.ref_url = 'comment url'
                    a.category = 'account'
                    a.save()
                    remember_me = False
                    if 'remember_me' in request.POST:
                        remember_me = True
                    self.start_session(user,remember_me=remember_me)
                    return self.returnurl_orgoto(controller='dashboard')
                else:
                    h.add_error("We were not able to verify that \
                        email or password, please try again")
            else:
                h.add_error("You did not submit a password, please try again.")
        else:
            h.add_error("You need to enter an email and password to signin.")
            
        return render('/account/signin.html')
    
    def logout(self):
        if not c.user:
             redirect_to(controller='home', action='index', id=None)
        response.delete_cookie('userkey')
        session.clear()
        h.add_alert("You have been signed out.")
        redirect_wsave(controller='home', action='index', id=None)
    
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
    
    @rest.dispatch_on(POST="account_edit")
    def edit(self):
        if not c.user:
             redirect_to(controller='home', action='index', id=None)
        else:
            c.person = meta.DBSession.query(Person).filter_by(
                    site_id=c.user.site_id, id=c.user.id).first()
        return render('/account/edit.html')
    
    @validate(schema=PersonEditValidation(), form='edit')
    def account_edit(self):
        """
        User has selected to update profile
        """
        if c.user and 'email' in request.POST:
            user = Person.get(c.user.site_id,c.user.id)
            user.displayname = request.POST['displayname']
            user.set_email(request.POST['email'])
            user.url = request.POST['url']
            self.start_session(user)
            user.save()
            c.person = user
            c.user = user
            self.start_session(user)
        return render('/account/settings.html')
    
    @validate(schema=PasswordChangeValidation(), form='edit')
    def change_pwd(self):
        if c.user:
            user = meta.DBSession.query(Person).filter_by(
                            email=c.user.email.lower()).first()
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
        return render('/account/settings.html')
    
    def settings(self):
        if not c.user:
             redirect_to(controller='home', action='index', id=None)
        else:
            c.person = meta.DBSession.query(Person).filter_by(
                site_id=c.user.site_id, id=c.user.id).first()
            return self._view(c.person,getcomments=True)
    
    def _view(self,person,getcomments=False):
        c.person = None
        if person:
            c.person = person
            #TODO, somehow filter by site???? this gets ALL
            if getcomments:
                c.comments = person.recent_comments(5)
            c.helptickets = c.person.help_tickets()
            c.activities_by_day = Activity.stats_by_person(person.site_id,person.id)
            if c.user is None:
                pass
            elif c.user is not None and c.user.issysadmin:
                pass
            elif c.user is not None and c.user.isadmin:
                pass
            else:
                if c.user.site_id == c.person.site_id:
                    pass
                else:
                    c.person = None
                    c.comments = None
        else:
            pass #TODO:  raise error, or bad page
        c.base_url = config['demisauce.url']
        return render('/account/settings.html')
    
    def viewh(self,id='blah'):
        person = meta.DBSession.query(Person).filter_by(
            hashedemail=id).first()
        return self._view(person,True)
    
    def view(self,id=0):
        if not c.user:
            redirect_to(controller='home', action='index', id=None)
        
        if c.user.issysadmin and id > 0:
            person = Person.get(-1,id)
        elif id > 0: 
            person = Person.get(c.user.site_id,id)
        
        return self._view(person,True)
    
    def view_mini(self,id=0):
        c.person = None
        if id > 0: # authenticated user
            person = Person.get(c.user.site_id,id)
            c.person = person
        return render('/account/profile_mini.html')
    


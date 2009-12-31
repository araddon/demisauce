import logging
import tornado
import json
from tornado.options import options
import tornado.escape
from datetime import datetime, timedelta
from sqlalchemy.sql import and_, or_, not_, func, select
import demisauce.model
from demisauce.model import meta
from demisauce.model.site import Site
from demisauce.model.activity import Activity
from demisauce.model.user import Person, Group, PersonValidation, \
    SignupForm, PersonEditValidation, InviteForm, GroupForm
from demisauce.lib import QueryDict, scheduler
from demisauce.model.comment import Comment
from demisauce.model.activity import Activity, add_activity
from formencode import Invalid, validators
from formencode.validators import *
import formencode, urllib
import demisaucepy.cache_setup
from demisaucepy.cache import cache
from demisauce.controllers import BaseHandler, RestMixin, SecureController, \
    send_emails
from gearman.task import Task

log = logging.getLogger(__name__)

def google_auth_url(return_url):
    import urllib
    from gdata import auth
    url = urllib.urlencode({'url':return_url})
    next = '%s/user/googleauth?%s' % (options.base_url,url)
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
    def options(self,action="",id=""):
        logging.debug("in Account api OPTIONS action=%s" % action)
        if action in ['pre_init_user','init_user']:
            return
        else:
            raise tornado.web.HTTPError(405)
    
    def googleauth(self,id=0):
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
        self.set_cookie('dsuserkey', user.user_uniqueid,expires_days=31)
        if 'url' in self.request.arguments:
            url = request.GET['url']
            self.redirect(str(url))
        self.render('/comment/comment_login.html')
    
    def index(self,id=0):
        if not self.user:
            return self.redirect('/user/signin')
        self.render('/user/settings.html')
    
    def inviteusers(self,id=0):
        self.render('/user/inviteusers.html')
    
    def inviteusers_POST(self,id=0):
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
                    url2 = urllib.quote_plus('/user/viewh/%s' % (user.hashedemail))
                    dnew = {}
                    dnew['link'] = '%s/user/verify?unique=%s&node=%s&return_url=%s' %\
                        (base_url(),user.user_uniqueid,user.id,url2)
                    dnew['from'] = self.user.displayname
                    a = Activity(site_id=user.site_id,person_id=user.id,activity='sending email invite')
                    a.ip = self.request.remote_ip 
                    a.ref_url = 'account admin invite'
                    a.category = 'account'
                    a.save()
                    scheduler.add_interval_task(send_emails,0,('invitation_to_demisauce',[user.email],dnew) , initialdelay=delay)
                    delay += 3
                
            return 'from form %s' % emails
        return 'error'
    
    def site_signup(self,id=''):
        if self.user:
            self.add_alert('Already signed in.')
            #redirect_wsave(action='index')
        elif 'invitecode' in self.request.arguments:
            self.user = meta.DBSession.query(Person).filter_by(
                        user_uniqueid=self.get_argument('invitecode')).first()
            
            invitecode = self.get_argument('invitecode')
        form = InviteForm(QueryDict(self.request.arguments))
        self.render('/user/sitesignup.html',invitecode=invitecode,form=form)
    
    def site_signup_POST(self,id=0):
        """
        User is signing up
        """
        user = meta.DBSession.query(Person).filter_by(
                    user_uniqueid=self.get_argument('invitecode').lower()).first()
        
        if user is None:
            self.add_error("We were not able to verify this invite, please \
                try again or enter your email in the top form for the waiting list.")
        form = InviteForm(QueryDict(self.request.arguments))
        if form and form.validate():
            user.set_password(form.password.data)
            user.site.name = form.sitename.data
            user.displayname = form.displayname.data
            user.verified = True
            user.isadmin = True
            model.setup_site(user)
            self.set_current_user(user,is_authenticated=True,islogon=True)
            user.save()
            self.add_alert('Account was created')
            
            return self.redirect('/home/index?msg=Account+was+created')
        else:
            self.add_error("errors in form")
        self.render('/user/sitesignup.html',form=form)
    
    def verify(self,id=0):
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
            
            if user is None:
                h.add_error("That link does not appear to be valid,\
                    please contact the person that invited you or sign up.")
                
                return redirect_wsave("/user/signup" )
                return self.signup()
            elif user.verified == True:
                # this user already registered
                h.add_alert('Already verified account')
                return redirect_wsave("/user/signin" )
            else:
                self.user = user
        self.render('/user/verify.html')
    
    def verify_POST(self,id=0):
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
                response.set_cookie('dsuserkey', user.user_uniqueid,
                                expires=datetime.today() + timedelta(days=31))
                self.start_session(user)
                user.save()
                
            else:
                h.add_error("You did not submit a password, please try again.")
            
            return self.returnurl_orgoto(controller='home',action='index')
        
        else:
            h.add_error("You need to enter an email and password to signin.")
        
        self.render('/user/signin.html')
    
    def verifycontinue(self,id=0):
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
        
        return self.redirect("/")
    
    def signup(self,id=0):
        user = self.get_current_user()
        form = SignupForm()
        if user:
            self.add_alert('Already signed in.')
            #redirect_wsave(action='index')
        self.render('/user/signup.html',form=form)
    
    def interest(self,id=0):
        """
        User has selected to enter an email to be on waitinglist
        """
        
        logging.debug(self.request.arguments)
        form = SignupForm(QueryDict(self.request.arguments))
        logging.debug(form.data)
        if 'email' in self.request.arguments and form.validate():
            user = meta.DBSession.query(Person).filter_by(
                    email=self.get_argument("email").lower()).first()
            
            if user is None:
                new_email = form.email.data.lower()
                site = Site(name=new_email,email=new_email)
                site.save()
                user = Person(site_id=site.id,email=new_email,
                              displayname=new_email)
                user.slug = user.hashedemail
                user.save()
                a = Activity(site_id=user.site_id,person_id=user.id,activity='Signup Interest Form')
                #a.ref_url = 'comment url'
                a.ip = self.request.remote_ip 
                a.category = 'account'
                a.save()
                
                link = '%s/user/verify?unique=%s&node=%s&return_url=%s' %\
                    (options.base_url,
                        user.user_uniqueid,
                        user.id,
                        urllib.quote_plus('/user/viewh/%s' % (user.hashedemail)))
                json_dict = {
                    'emails':[user.email],
                    'template_name':'thank_you_for_registering_with_demisauce',
                    'template_data':{
                        'link':link,
                        'displayname':user.displayname,
                        'email':user.email,
                        'title':'welcome'
                    }
                }
                self.db.gearman_client.do_task(Task("email_send",json.dumps(json_dict), background=True))
                
            self.add_alert("Thank You!")
            self.redirect("/")
        
        return self.render('/user/signup.html',form=form)
    
    def signin(self,id=0):
        log.info('made it to account signin?' )
        email = None
        if self.get_current_user():
            return self.redirect("/home/index")
        elif 'dsuserkey' in self.cookies:
            user = meta.DBSession.query(Person).filter_by(
                    user_uniqueid=self.get_cookie('dsuserkey').lower()).first()
            
            if user:
                a = Activity(site_id=user.site_id,person_id=user.id,activity='Logging In')
                #a.ref_url = 'comment url'
                a.category = 'account'
                a.ip = self.request.remote_ip 
                self.set_current_user(user)
                return self.redirect('/home/default')
        
        if 'email' in self.cookies:
            email = self.get_cookie('email').lower()
                            
        googleurl = google_auth_url('%s/user/usersettings' % options.base_url)
        self.render('/user/signin.html',google_auth_url=googleurl,email=email)
    
    def signin_POST(self,id=0):
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
                    a.ip = self.request.remote_ip 
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
            
        self.render('/user/signin.html')
    
    def logout(self,id=0):
        if not self.user:
             self.redirect("/")
        self.clear_cookie('dsuserkey')
        self.clear_cookie('dsuser')
        self.redirect("/")
    
    def handshake(self,id=0):
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
            #urllib.urlencode({'return_url':'http://localhost:4951/user/handshake'})
            print 'redirecting for handshake url=%s' % url
            # http://demisauce.test:8001/handshake/initial?return_url=http%3A%2F%2Flocalhost%3A4951%2Faccount%2Fhandshake&token=yourtoken
            #redirect_to('http://demisauce.test:8001/handshake/initial?return_url=http%3A%2F%2Flocalhost%3A4951%2Faccount%2Fhandshake&token=%s' % apiuser.hashed_email)
            return redirect_to(url)
        """
    
    def edit(self,id=0):
        if not self.user:
             redirect_to(controller='home', action='index', id=None)
        else:
            person = meta.DBSession.query(Person).filter_by(
                    site_id=self.user.site_id, id=self.user.id).first()
            
        self.render('/user/edit.html',person=person)
    
    def account_edit(self,id=0):
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
        self.render('/user/settings.html')
    
    def change_pwd(self,id=0):
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
        self.render('/user/settings.html')
    
    def usersettings(self,id=0):
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
        self.render('/user/settings.html',person=person,helptickets=helptickets,
            activities_by_day=activities_by_day,activity_count=activity_count)
    
    def viewh(self,id='blah'):
        person = meta.DBSession.query(Person).filter_by(hashedemail=id).first()
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
        person = None
        if id > 0:
            person = Person.get(self.user.site_id,id)
        self.render('/user/profile_mini.html',person=person)
    


class GroupController(RestMixin,BaseHandler):
    def index(self,id=0):
        return self.viewlist()
    
    def ajaxget(self,id=''):
        if 'q' in self.request.arguments:
            q = self.get_argument("q")
            pl = meta.DBSession.query(Person).filter(or_(
                Person.displayname.like('%' + q + '%'),
                Person.email.like('%' + q + '%'))).limit(20)
        else:
            pl = meta.DBSession.query(Person).limit(20)
        s = ''
        for p in pl:
            s += "%s|%s\n" % (p.displayname,p.email)
        self.write(s)
    
    def viewlist(self,id=0):
        item = None
        groups = Group.by_site(self.user.site_id)
        temp = """
        filter = 'all'
        if 'filter' in request.params:
            filter = request.params['filter']
        page = 1
        if 'page' in request.params:
            page = int(request.params['page'])
        c.groups = webhelpers.paginate.Page(
                Group.by_site(self.user.site_id),
                page=page,items_per_page=5)
                
        ${h.dspager(c.groups)}
        groups = h.dspager(groups)
        """
        
        
        self.render('/user/group.html',action='list',groups=groups)
    
    def view(self,id=0):
        item = Group.get(self.user.site_id,id)
        if not item or not item.site_id == self.user.site_id:
            item = None
        self.render('user/group.html',action='view',item=item)
    
    def addedit(self,id=0):
        return self.viewlist(id)
    
    def addedit_post(self,id=''):
        g = None
        form = GroupForm(QueryDict(self.request.arguments))
        print form.data
        if form and form.validate():
            if 'id' in self.request.arguments and self.get_argument("id") != '0':
                g = Group.get(self.user.site_id,int(self.get_argument("id")))
                g.name = form.name.data
            else:
                g = Group(self.user.site_id,form.name.data)
            
            newtogroup, newtosite = g.add_memberlist(form.members.data)
            g.save()
        #return 'newtogroup= %s,  \n newtosite=%s' % (newtogroup, newtosite)
        return self.viewlist()
        
    
    #@rest.dispatch_on(POST="group_popup_submit")
    def popup(self,id=0):
        item = Group()
        self.render('/user/group_popup.html',action='edit',item=item)
    
    def popup_view(self,id=0):
        item = Group.get(self.user.site_id,id)
        if not item.site_id == self.user.site_id:
            item = None
        self.render('/user/group_popup.html',action='view',item=item)
    
    #@validate(schema=GroupFormValidation(), form='popup')
    def popup_post(self,id=''):
        g = None
        form = GroupForm(QueryDict(self.request.arguments))
        if form and form.validate():
            if 'id' in self.request.arguments and self.get_argument("id") != '0':
                g = Group.get(self.user.site_id,int(self.get_argument("id")))
                g.name = form.name.data
            else:
                g = Group(self.user.site_id,form.name.data)
            
            newtogroup, newtosite = g.add_memberlist(form.members.data)
            g.save()
        #return 'newtogroup= %s,  \n newtosite=%s' % (newtogroup, newtosite)
        self.popup_view(g.id)
    
    def edit(self,id=0):
        item = Group.get(self.user.site_id,id)
        if not item or not item.site_id == self.user.site_id:
            item = None
        self.render('/user/group.html',action='edit',item=item)


_controllers = [
    (r"/user/group/(.*?)/(.*?)/", GroupController),
    (r"/user/group/(.*?)/(.*?)", GroupController),
    (r"/user/group/(.*?)", GroupController),
    (r"/user/(.*?)/(.*?)/", AccountController),
    (r"/user/(.*?)/(.*?)", AccountController),
    (r"/user/(.*?)", AccountController),
]
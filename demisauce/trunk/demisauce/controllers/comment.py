#!/usr/bin/env python
import logging, urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
from demisauce.lib.base import *
import demisauce.lib.sanitize
from demisauce import model
from demisauce.model import meta, mapping
from demisauce.model.comment import *
from demisauce.model.site import Site
from datetime import datetime, timedelta


log = logging.getLogger(__name__)

def google_auth_url(return_url):
    import urllib
    from gdata import auth as gauth
    url = urllib.urlencode({'url':return_url})
    return gauth.GenerateAuthSubUrl('%s/comment/googleauth?%s' % (config['demisauce.url'],url), 
            'http://www.google.com/m8/feeds',False,True)

def compute_userhash():
    if 'HTTP_USER_AGENT' in request.environ and 'REMOTE_ADDR' in request.environ:
        hash = request.environ['HTTP_USER_AGENT'] + request.environ['REMOTE_ADDR'] 
        import hashlib
        return hashlib.md5(hash + config['demisauce.apikey']).hexdigest()
    else:
        return None

class LogonFormValidation(formencode.Schema):
    """Form validation for the comment web admin"""
    allow_extra_fields = True
    filter_extra_fields = False
    email = formencode.All(String(not_empty=True))

class CommentFormValidation(formencode.Schema):
    """Form validation for the comment web admin"""
    allow_extra_fields = True
    filter_extra_fields = False
    authorname = formencode.All(String(not_empty=True))
    email = formencode.All(String(not_empty=True))
    comment = formencode.All(String(not_empty=True))

class CommentController(BaseController):
    def __before__(self):
        BaseController.__before__(self)
        if 'site_key' in request.params:
            site_key = request.params['site_key']
            site = meta.DBSession.query(model.site.Site).filter_by(key=str(site_key)).first()
            if site:
                c.site = site
                c.site_key = site.key
    
    def index(self,id=0):
        if id > 0:
            c.items = [meta.DBSession.query(Comment).get(id)]
        elif c.user:
            c.items = Comment.by_site(c.user.site_id)
        return render('/comment/comment.html')
        
    def add(self,id=0):
        cmt = Comment(1)
        cmt.set_user_info(c.user)
        cmt.comment = request.params['comment']
        cmt.uri = '/comment/comment.html'
        cmt.save()
    
    def googleauth(self):
        """
        User is coming in from google, should have an auth token
        """
        # NEED SITE????  Or does that not make sense?
        import gdata
        import gdata.contacts
        import gdata.contacts.service
        authsub_token = request.GET['token']
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
            user = Person(1,email,name)
            user.authn = 'google'
            user.save()
        response.set_cookie('userkey', user.user_uniqueid,
                            expires=datetime.today() + timedelta(days=31))
        if 'url' in request.GET:
            url = request.GET['url']
            redirect_to(str(url))
        return render('/comment/comment_login.html')
    
    def delete(self,id=0):
        if c.user and c.user.isadmin and id > 0:
            item = Comment.get(c.user.site_id,id)
            if item:
                item.delete()
    
    @rest.dispatch_on(POST="commentsubmit")
    def commentform(self,slug=0):
        if request.GET.has_key('url'):
            c.goto_url =  request.GET['url']
        else:
            if c.user:
                c.goto_url = c.user.url
            else:
                c.goto_url = 'http://www.google.com'
        
        return render('/comment/comment_commentform.html')
    
    @validate(schema=CommentFormValidation(), form='commentform')
    def commentsubmit(self,id=''):
        site = Site.by_slug(str(id))
        if site:
            c.site = site
            item = Comment(site.id)
            if c.user:
                item.set_user_info(c.user)
            else:
                item.authorname = sanitize.Sanitize(self.form_result['authorname'])
                item.blog = sanitize.Sanitize(self.form_result['blog'])
                if self.form_result.has_key('email'):
                    item.set_email(sanitize.Sanitize(self.form_result['email']))
                if item.blog == "your blog url":
                    item.blog = ''
            if 'HTTP_X_FORWARDED_FOR' in request.environ:
                item.ip = request.environ['HTTP_X_FORWARDED_FOR']
            elif 'REMOTE_ADDR' in request.environ:
                item.ip = request.environ['REMOTE_ADDR']
            
            item.comment = sanitize.Sanitize(self.form_result['comment'])
            if self.form_result.has_key('type'):
                item.type = sanitize.Sanitize(self.form_result['type'])
            else:
                item.type = 'blogentry'
            
            if self.form_result.has_key('goto'):
                dest = self.form_result['goto']
                item.uri = dest
            elif c.user:
                dest = c.user.url
            else:
                #TODO panic?
                return
            
            item.save()
            
            #send emails
            from demisauce.lib import scheduler
            dnew = {'sitename':c.site.name,'displayname':item.authorname,
                'email':item.email, 'url':dest,'blog':item.blog}
            scheduler.add_interval_task(send_emails,0,('comment-notification',[c.site.email],dnew) , initialdelay=4)
            # TODO  '?#demisauce-comments'
            c.goto_url = dest
            return render('/refresh.html')
        else:
            #TODO panic?
            pass
        return
    
    def js(self,id=''):
        #ok, lets create cookie
        hash = compute_userhash()
        if hash != None:
            response.set_cookie('commentorhash', hash,
                        expires=datetime.today() + timedelta(hours=1))
        c.hash = hash
        #response.headers['Content-Type'] = 'text/html'
        return render('/comment/comment_js.js')
    
    def logout(self):
        response.delete_cookie('userkey')
        session.clear()
        return self.login()
    
    def login(self,id=0):
        if 'url' in request.GET:
            c.return_url = request.GET['url']
        else:
            c.return_url = 'http://www.demisauce.com'
        c.google_auth_url = google_auth_url(c.return_url)
        return render('/comment/comment_login.html')
    
    @validate(schema=LogonFormValidation(), form='login')
    def loginpost(self,id=0):
        if 'email' in request.POST:
            user = meta.DBSession.query(Person).filter_by(
                        email=request.POST['email'].lower()).first()
            
            if user is None:
                c.message = "We were not able to verify that email\
                     or password, please try again"
                return render('/comment/comment_login.html')
            elif 'password' in request.POST:
                if user.is_authenticated(request.POST['password']):
                    response.set_cookie('userkey', user.user_uniqueid,
                                    expires=datetime.today() + timedelta(days=31))
                else:
                    c.message = "We were not able to verify that email\
                         or password, please try again"
                    return render('/comment/comment_login.html')
            else:
                c.message = "You did not submit a password, please try again."
                return render('/comment/comment_login.html')
        else:
            c.message = "You need to enter an email and password to signin."
            return render('/comment/comment_login.html')
        
        c.goto_url = request.POST['goto']
        return render('/refresh.html')
    
    def js2(self,id=''):
        slug = id
        hash = compute_userhash()
        # verify that they 
        if hash != None and 'url' in request.params:
            site = Site.by_slug(str(slug))
            url = str(request.params['url'])
            url = url[:url.find('/',8)]
            if site and len(url) > 5 and url in site.site_url:
                # filter comments for just url being requested
                c.site = site
                c.url = str(request.params['url'])
                c.items = Comment.for_url(site,request.params['url'])
                return render('/comment/comment_js2.js')
            else:
                print '%s not in site_url' % (url)
        else:
            print 'url not in params'
        
        return """document.getElementById('demisauce-comments').innerHTML = '<a href="%s/">Sorry Go to Demisauce to Comment</a>';""" % c.base_url
    


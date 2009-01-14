#!/usr/bin/env python
import logging, urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
from demisauce.lib.base import *
#import demisauce.lib.sanitize
from demisauce.lib.helpers import dspager
from demisauce import model
from demisauce.model import meta, mapping, activity
from demisauce.model.comment import *
from demisauce.model.site import Site
from datetime import datetime, timedelta
import simplejson


log = logging.getLogger(__name__)

def google_auth_url(return_url):
    import urllib
    from gdata import auth
    url = urllib.urlencode({'url':return_url})
    next = '%s/comment/googleauth?%s' % (config['demisauce.url'],url)
    scope = 'http://www.google.com/m8/feeds'
    auth_sub_url = auth.GenerateAuthSubUrl(next, scope, secure=False, session=True)
    return auth_sub_url

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
            c.items = dspager(Comment.by_site(c.user.site_id))
        return render('/comment/comment.html')
    
    def googleauth(self):
        """
        User is coming in from google, should have an auth token
        """
        # NEED SITE????  Or does that not make sense?
        import gdata
        import gdata.contacts
        import gdata.contacts.service
        authsub_token = request.GET['token']
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
            
        expires_seconds = 60*60*24*31
        response.set_cookie('userkey', user.user_uniqueid,
                            expires=expires_seconds)
        if 'url' in request.GET:
            url = request.GET['url']
            redirect_to(str(url))
        return render('/comment/comment_login.html')
    
    @requires_role('admin')
    def delete(self,id=0):
        if c.user and c.user.isadmin and id > 0:
            item = Comment.get(c.user.site_id,id)
            if item:
                item.delete()
    
    @rest.dispatch_on(POST="commentsubmit")
    def commentform(self,id=0):
        site = Site.by_slug(str(id))
        c.source = 'js'
        if site and site.id > 0:
            c.site_slug = site.slug
            c.site = site
            if 'source' in request.params:
                c.source = request.params['source']
            c.resource_id = ''
            if 'rid' in request.params:
                c.resource_id = request.params['rid']
            if request.GET.has_key('url'):
                c.goto_url =  request.GET['url']
            else:
                if c.user:
                    c.goto_url = c.user.url
                else:
                    c.goto_url = 'http://www.google.com'
        else:
            raise Exception('that site was not found')
        #c.hasheader = False
        #c.isblue = True
        return render('/comment/comment_commentform.html')
    
    @validate(schema=CommentFormValidation(), form='commentform')
    def commentsubmit(self,id=''):
        site = Site.by_slug(str(id))
        if site:
            c.site = site
            item = Comment(site_id=site.id)
            if c.user:
                item.set_user_info(c.user)
                a = activity.Activity(site_id=c.user.site_id,person_id=c.user.id,activity='Commenting')
                #a.ref_url = 'comment url'
                a.category = 'comment'
                a.save()
            else:
                item.authorname = sanitize(self.form_result['authorname'])
                item.blog = sanitize(self.form_result['blog'])
                if self.form_result.has_key('email'):
                    item.set_email(sanitize(self.form_result['email']))
                if item.blog == "your blog url":
                    item.blog = ''
            # prod environment proxy: apache
            if 'HTTP_X_FORWARDED_FOR' in request.environ:
                item.ip = request.environ['HTTP_X_FORWARDED_FOR']
            elif 'REMOTE_ADDR' in request.environ:
                item.ip = request.environ['REMOTE_ADDR']
            
            item.comment = sanitize(self.form_result['comment'])
            if self.form_result.has_key('type'):
                item.type = sanitize(self.form_result['type'])
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
                
            if 'rid' in self.form_result:
                item.uri = self.form_result['rid'].lower()
            
            item.save()
            
            #send emails
            from demisauce.lib import scheduler
            dnew = {'sitename':c.site.name,'displayname':item.authorname,
                'email':item.email, 'url':dest,'blog':item.blog}
            scheduler.add_interval_task(send_emails,0,('comment-notification',[c.site.email],dnew) , initialdelay=4)
            # TODO  '?#demisauce-comments'
            c.goto_url = dest
            c.resource_id = ''
            if 'rid' in self.form_result:
                c.resource_id = self.form_result['rid']
            source = 'js'
            if 'source' in self.form_result:
                source = self.form_result['source']
            if 'jsoncallback' in request.params:
                data = {'success':True,'html':item.comment}
                json = simplejson.dumps(data)
                response.headers['Content-Type'] = 'text/json'
                return '%s(%s)' % (request.params['jsoncallback'],json)
            #if source == 'js':
            #    return render('/refresh.html')
            #else:
            c.items = [item]
            #c.show_form = False
            return render('/comment/comment_nobody.html')
        else:
            #TODO panic?
            raise 'eh'
            pass
        return
    
    def commentsubmitjsonp(self,id=''):
        site = Site.by_slug(str(id))
        if site:
            c.site = site
            item = Comment(site_id=site.id)
            if c.user:
                item.set_user_info(c.user)
                a = activity.Activity(site_id=c.user.site_id,person_id=c.user.id,activity='Commenting')
                #a.ref_url = 'comment url'
                a.category = 'comment'
                a.save()
            else:
                if 'authorname' in request.params:
                    item.authorname = sanitize(request.params['authorname'])
                if 'blog' in request.params:
                    item.blog = sanitize(request.params['blog'])
                if 'email' in request.params:
                    item.set_email(sanitize(request.params['email']))
                if item.blog == "your blog url":
                    item.blog = ''
            
            # prod environment proxy: apache
            if 'HTTP_X_FORWARDED_FOR' in request.environ:
                item.ip = request.environ['HTTP_X_FORWARDED_FOR']
            elif 'REMOTE_ADDR' in request.environ:
                item.ip = request.environ['REMOTE_ADDR']
            
            if 'comment' in request.params:
                item.comment = sanitize(request.params['comment'])
            if 'type' in request.params:
                item.type = sanitize(request.params['type'])
            else:
                item.type = 'blogentry'
            
            if 'rid' in request.params:
                item.uri = urllib.unquote_plus(request.params['rid'].lower())
            
            item.save()
            
            #send emails
            from demisauce.lib import scheduler
            dnew = {'sitename':c.site.name,'displayname':item.authorname,
                'email':item.email, 'url':'dest','blog':item.blog}
            scheduler.add_interval_task(send_emails,0,('comment-notification',[c.site.email],dnew) , initialdelay=4)
            
            if 'jsoncallback' in request.params:
                c.items = [item]
                data = {'success':True,'html':render('/comment/comment_nobody.html')}
                json = simplejson.dumps(data)
                response.headers['Content-Type'] = 'text/json'
                return '%s(%s)' % (request.params['jsoncallback'],json)
        else:
            #TODO panic?
            raise 'eh'
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
                log.error('%s not in site_url' % (url))
        else:
            log.info('not in site_url' )
        
        return """document.getElementById('demisauce-comments').innerHTML = '<a href="%s/">Sorry Go to Demisauce to Comment</a>';""" % c.base_url
    


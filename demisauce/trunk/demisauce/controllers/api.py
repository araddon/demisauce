#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
import simplejson
from sqlalchemy.orm import eagerload

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import meta, help, cms, person, \
    group, poll
from demisauce.model.site import Site
from demisauce.model.comment import Comment
from demisauce.model.email import Email
from paste.httpexceptions import HTTPException
from paste.wsgiwrappers import WSGIResponse

log = logging.getLogger(__name__)

class RestApiMethod(RestMethod):
    def __call__(self,**kwargs):
        if 'format' in kwargs:
            format = kwargs['format']
            if format == 'json':
                response.headers['Content-Type'] = 'text/json'
            elif format == 'xml':
                response.headers['Content-Type'] = 'application/xhtml+xml'
            else: 
                pass # html, view
        return RestMethod.__call__(self,**kwargs)
    


def requires_site(target):
    """A decorator to protect the API methods to be able to
    accept api by either apikey or logged on user, in future oath?
    """
    def decorator(self,*args,**kwargs):
        site = get_current_site() 
        if not site:
            log.info('403, api call ' )
            return self.nokey()
        else:
            if 'format' in kwargs and 'id' in kwargs:
                return target(self,format=kwargs['format'], id=kwargs['id'])
            elif 'format' in kwargs:
                return target(self,format=kwargs['format'])
            else:
                return 'bad decorator'
    return decorator

def requires_site_slug(target):
    """allows access with only a slug which identifies a site
    but isn't really secure  """
    def decorator(self,*args):
        site = get_current_site() 
        if not site:
            log.info('403, api call ' )
            return self.nokey()
        else:
            return target(self,*args)
    return decorator

class ApiController(BaseController):
    def __before__(self):
        BaseController.__before__(self)
        
        # Authentication required?
        if self.site and self.site.id > 0:
            request.environ['api.isauthenticated'] = 'true'
            request.environ['site'] = self.site
        else:
            log.debug('no apikey or c.user')
    
    def nokey(self):
        """
        returns error code for no api key
        """
        response.headers['Content-Type'] = 'application/xhtml+xml'
        return "<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n" + \
                "<exception id=\"401\" >Invalid API Key</exception>" 
    
    def connect(self,format='html',id=''):
        """
        Used by clients to test connectivity
        returns
            'connected, valid api key' if api key is valid
            'invalid api key but connected' if api key isn't valid
        """
        if self.site and self.site.id > 0:
            return 'connected, valid api key'
        else:
            return 'invalid api key but connected'
    
    @requires_site
    def cms(self,format='html',id=''):
        if not 'site' in request.environ:
            return self.nokey()
        
        c.len = 0
        from demisauce.model.cms import Cmsitem
        if id != '' and id != None:
            rid = urllib.unquote_plus(id)
            c.cmsitems = meta.DBSession.query(Cmsitem).filter_by(rid=rid).all()
            if (c.cmsitems and len(c.cmsitems) == 1) and \
                (c.cmsitems[0].item_type == "folder" or \
                c.cmsitems[0].item_type == 'root'):
                c.cmsitems = [itemassoc.item for itemassoc in c.cmsitems[0].children]
        else:
            c.cmsitems = meta.DBSession.query(Cmsitem).all()
        
        c.resource_id = id
        if c.cmsitems == []:
            log.debug('404, no items rid=%s' % id)
            abort(404, 'No items found')
        
        if format == 'html':
            return render('/api/cms.html')
        elif format == 'xml':
            response.headers['Content-Type'] = 'application/xhtml+xml'
            c.len = len(c.cmsitems)
            return render('/api/cms.xml')
        elif format == 'script':
            return render('/api/cmsjs.js')
        else:
            raise 'not implemented'
    
    @requires_site
    def help(self,format='script',id=''):
        if id != '' and id != None:
            rid = urllib.unquote_plus(id)
            c.cmsitems = meta.DBSession.query(cms.Cmsitem).filter_by(rid=rid).all()
            if (c.cmsitems and len(c.cmsitems) == 1) and \
                (c.cmsitems[0].item_type == "folder" or \
                c.cmsitems[0].item_type == 'root'):
                c.cmsitems = [itemassoc.item for itemassoc in c.cmsitems[0].children]
            
        if c.site and c.site.id:
            url = id.replace('root/help','')
            topinfo = help.HelpResponse.for_url(c.site,url,5)
            c.topinfo = [hr for hr in topinfo] # get something that can do a len()
            log.debug('url=%s, topinfo = %s' % (url,c.topinfo))
        
        c.resource_id = id
        results = render('/api/cms.html')
        data = {'success':True,'html':results,'key':id}
        json = simplejson.dumps(data)
        if format == 'json':
            response.headers['Content-Type'] = 'text/json'
            return '%s(%s)' % (request.params['jsoncallback'],json)
        else:
            return results
        #return render('/api/cmsjs.js')
    
    @requires_site
    def comment(self,format='json',id=''):
        site = request.environ['site']
        #site2 = Site.by_slug(str(id))
        #if site2.id != site.id and 'apikey' in request.params and request.params['apikey'] == site2.key:
        #    site = site2 # logged in user not same as 
        c.len = 0
        
        if id != '' and id != None:
            rid = urllib.unquote_plus(id)
            log.info('comment rid= %s' % id)
            c.comments = Comment.for_url(site_id=site.id,url=rid)
        else:
            c.comments = Comment.all(site.id)
        
        c.items = c.comments
        c.resource_id = urllib.quote_plus(id)
        
        if format == 'html':
            return render('/api/comment.html')
        elif format == 'xml':
            response.headers['Content-Type'] = 'application/xhtml+xml'
            if c.comments == []:
                #log.info('404, no comments siteid=%s, uri=%s' %(site.id,rid))
                #abort(404, 'No items found')
                c.len = 0 # no comments is ok, right?
            else:
                c.len = len(c.comments)
            return render('/api/comment.xml')
        elif format == 'view':
            c.show_form = True
            c.source = 'remote_html'
            c.len = len(c.comments)
            c.hasheader = True
            c.site_slug = site.slug
            #raise 'eh'
            return render('/comment/comment_nobody.html')
        elif format == 'json':
            return render('/api/comment.js')
        else:
            raise NotImplementedError('format of type %s not supported' % format)
    
    @requires_site
    def email(self,format='html',id='',**kw):
        site = request.environ['site']
        class email(RestApiMethod):
            def get(self, **kw):
                return render('/api/email.xml')
            def post(self, **kw):
                return 'not implemented'
            def put(self, **kw):
                return 'not implemented'
            def delete(self, **kw):
                return 'not implemented'
        
        if id != '' and id != None:
            c.emailtemplates = Email.by_key(site_id=site.id,key=id)  
            if c.emailtemplates:
                c.item = c.emailtemplates
                c.emailtemplates = [c.item]       
        else:
            c.emailtemplates = Email.all(site_id=site.id)
        
        if not c.emailtemplates:
            log.info('no email templates?  Should be site=%s' % site)
        
        kw.update({'format':format})
        return email()(**kw)
    
    @requires_site
    def send_email(self,format='xml',id=''):
        """
        Sends an email, accepts dictionary of info
        that it will hash into email to send
        """
        if not 'site' in request.environ:
            return self.nokey()
        
        if id != '' and id != None:
            site = request.environ['site']
            email = Email.by_key(site.id,id)
            if email:
                c.item = email
            
    
    #@requires_site
    def service(self,format='xml',id='',**kw):
        #site = request.environ['site']
        class servicerest(RestApiMethod):
            def get(self, **kw):
                return render('/api/service.xml')
            def post(self, **kw):
                return 'not implemented'
            def put(self, **kw):
                return 'not implemented'
            def delete(self, **kw):
                return 'not implemented'
        
        if id != '' and id != None:
            app,service = id.split('/')
            services = model.service.Service.by_app_service(appkey=app,servicekey=service)  
            if services:
                c.services = [services]       
        else:
            c.services = model.service.Service.all()
        
        if not c.services:
            log.info('no services?  Should be id=%s' % id)
        
        kw.update({'format':format})
        return servicerest()(**kw)
    
    @requires_site
    def person(self,format='xml',id=''):
        if c.site:
            verb = request.environ['REQUEST_METHOD'].lower()
            p = None
            if verb == 'get':
                if id == '' or id == None:
                    c.persons = person.Person.by_site(c.site.id)
                else:
                    p = person.Person.by_hashedemail(c.site.id,id)
                    c.persons = [p]
            elif verb == 'post' or verb == 'put':
                postvals = {}
                p = person.Person.by_hashedemail(c.site.id,id)
                for pkey in request.params:
                    postvals[pkey] = request.params[pkey]
                if p == None: # new not edit
                    p = person.Person(site_id=c.site.id,email=request.params['email'])
                if 'authn' in request.params:
                    p.authn = request.params['authn']
                if 'displayname' in request.params:
                    p.displayname = request.params['displayname']
                p.save()
                c.persons = [p]
            elif verb == 'delete':
                return 'delete'
            else:
                return 'what?'
            response.headers['Content-Type'] = 'application/xhtml+xml'
            
            return render('/api/person.xml')
        else:
            log.info('person: no site key %s' % (c.site))
            return 'no site key'
    
    @requires_site
    def group(self,format='xml',id=0, **kwargs):
        if c.site:
            verb = request.environ['REQUEST_METHOD'].lower()
            g = group.Group.get(c.site.id,id)
            if not g or not g.site_id == c.site.id:
                #g = None
                return 'crap %s' % id
            if verb == 'get':
                pass
            elif verb == 'post' or verb == 'put':
                postvals = {}
                for pkey in request.params:
                    postvals[pkey] = request.params[pkey]
                else:
                    g = group.Group(c.site.id,request.params['name'])
                if 'authn' in request.params:
                    g.authn = request.params['authn']
                if 'displayname' in request.params:
                    g.displayname = request.params['displayname']
                g.save()
            elif verb == 'delete':
                return 'delete'
            else:
                return 'what?'
            response.headers['Content-Type'] = 'application/xhtml+xml'
            c.groups = [g]
            return render('/api/group.xml')
        else:
            return 'no site key'
    
    @requires_site
    def poll(self,format='xml',id='',**kw):
        site = request.environ['site']
        if site:
            p = None
            c.polls = None
            if id != '' and id != None:
                id = str(urllib.unquote_plus(id))
            
            if id == '' or id == None:
                c.polls = poll.Poll.by_site(site.id)
            else:
                p = poll.Poll.by_key(site.id,id)
                if type(p) != list:
                    c.polls = [p]
            class pollrest(RestApiMethod):
                def get(self, **kw):
                    return render('/api/poll.xml')
                def post(self, **kw):
                    raise NotImplementedError('not implemented')
                def put(self, **kw):
                    raise NotImplementedError('not implemented')
                def delete(self, **kw):
                    raise NotImplementedError('not implemented')
            
            if format == 'xml':
                response.headers['Content-Type'] = 'application/xhtml+xml'
            elif p is not None and format == 'view':
                return '%s %s' % (p.html,p.results)
            kw.update({'format':format})
            return pollrest()(**kw)
        else:
            return 'no site key'
    

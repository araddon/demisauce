#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
from sqlalchemy.orm import eagerload

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import meta, help, cms, person, \
    group, poll
from demisauce.model.email import Email
from paste.httpexceptions import HTTPException
from paste.wsgiwrappers import WSGIResponse


log = logging.getLogger(__name__)

class ApiController(BaseController):
    def __before__(self):
        BaseController.__before__(self)
        #log.error('API' + request.environ["PATH_INFO"])
        # Authentication required?
        if 'apikey' in request.params:
            apikey = request.params['apikey']
            site = meta.DBSession.query(model.site.Site).filter_by(key=apikey).first()
            if site and site.id > 0:
                request.environ['api.isauthenticated'] = 'true'
                request.environ['api.site'] = site
            c.site = site
        elif c.user:
            request.environ['api.site'] = c.user.site
            request.environ['api.isauthenticated'] = 'true'
            c.site = c.user.site
        else:
            log.debug('no apikey or c.user')
        
        c.demisauce_url = config['demisauce.url']
    
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
        apikey = request.params['apikey']
        site = meta.DBSession.query(model.site.Site).filter_by(key=apikey).first()
        if site and site.id > 0:
            return 'connected, valid api key'
        else:
            return 'invalid api key but connected'
    
    def cms(self,format='html',id=''):
        if not 'api.site' in request.environ:
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
            return render('/api/cmshtml.mako')
        elif format == 'xml':
            response.headers['Content-Type'] = 'application/xhtml+xml'
            c.len = len(c.cmsitems)
            return render('/api/cmsxml.mako')
        elif format == 'script':
            return render('/api/cmsjs.js')
        else:
            raise 'not implemented'
    
    def help(self,format='script',id=''):
        if not 'api.site' in request.environ:
            return self.nokey()
        
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
        return render('/api/cmsjs.js')
    
    def comment(self,format='html',id=''):
        from demisauce.model.comment import Comment
        c.items = meta.DBSession.query(Comment).all()
        for comment in c.items:
            print comment.uri
        return 'hello'
    
    def email(self,format='html',id=''):
        if not 'api.site' in request.environ:
            return self.nokey()
        
        if id != '' and id != None:
            site = request.environ['api.site']
            c.emailtemplates = meta.DBSession.query(Email).filter_by(
                site_id=site.id,key=id).all()
            
            if c.emailtemplates:
                c.item = c.emailtemplates[0]
            else:
                print 'argh, no email template, siteid = %s' % site.id
        else:
            site = request.environ['api.site']
            c.emailtemplates = meta.DBSession.query(Email).filter_by(
                site_id=site.id).all()
        
        if c.emailtemplates and 'api.isauthenticated' in request.environ:
            if c.emailtemplates[0].site.key == request.environ['api.site'].key:
                response.headers['Content-Type'] = 'application/xhtml+xml'
                return render('/api/email.mako')
            else:
                print 'c.emaltemplates.key=%s   site.key=%s' % (c.emailtemplates[0].site.key,
                    request.environ['api.site'].key)
                abort(401, 'Invalid API Key')
        
        #TODO be a bit nicer with valid xml and error codes
        return "not correct key"
    
    def send_email(self,format='xml',id=''):
        """
        Sends an email, accepts dictionary of info
        that it will hash into email to send
        """
        if not 'api.site' in request.environ:
            return self.nokey()
        
        if id != '' and id != None:
            site = request.environ['api.site']
            email = Email.by_key(site.id,id)
            if email:
                c.item = email
            
    
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
                if not p == None:
                    print 'p not none %s' % p
                else:
                    print 'p is none %s' % id
                    p = person.Person(c.site.id,request.params['email'])
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
            print 'person no site key %s' % (c.site)
            return 'no site key'
    
    def group(self,format='xml',id=''):
        if c.site:
            verb = request.environ['REQUEST_METHOD'].lower()
            g = group.Group.get(c.site.id,id)
            if not g.site_id == c.site.id:
                g = None
                return
            if verb == 'get':
                pass
            elif verb == 'post' or verb == 'put':
                postvals = {}
                for pkey in request.params:
                    postvals[pkey] = request.params[pkey]
                if not g == None:
                    print 'group not new %s' % g.name
                else:
                    print 'group is new'
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
    
    def poll(self,format='xml',id=''):
        if c.site:
            if id != '' and id != None:
                id = urllib.unquote_plus(id)
            verb = request.environ['REQUEST_METHOD'].lower()
            if verb == 'get':
                if id == '' or id == None:
                    c.polls = poll.Poll.by_site(c.site.id)
                else:
                    p = poll.Poll.by_key(c.site.id,id)
                    if type(p) != list:
                        p = [p]
                    c.polls = p
            elif verb == 'post' or verb == 'put':
                postvals = {}
                p = poll.Poll.get(c.site.id,id)
                if not p.site_id == p.site.id:
                    p = None
                    return
                for pkey in request.params:
                    postvals[pkey] = request.params[pkey]
                if not p == None:
                    print 'poll not new %s' % p.name
                else:
                    print 'poll is new'
                    p = poll.Poll(c.site.id,request.params['name'])
                    
                        
                if 'description' in request.params:
                    p.description = request.params['description']
                p.save()
                c.polls = [p]
            elif verb == 'delete':
                return 'delete'
            else:
                return 'what?'
            response.headers['Content-Type'] = 'application/xhtml+xml'
            
            return render('/api/poll.xml')
        else:
            return 'no site key'
    

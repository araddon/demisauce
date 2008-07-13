"""The base Controller API

Provides the BaseController class for subclassing, and other objects
utilized by Controllers.
"""
import logging, time, cgi
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, validate, rest
from pylons.i18n import _, ungettext, N_
from pylons.templating import render

import demisauce.lib.helpers as h
import demisauce.lib.sanitize as libsanitize
import demisauce.model as model
from demisauce.model import mapping, meta
from demisauce.model.person import Person
import tempita

log = logging.getLogger(__name__)

# create scheduler
from demisauce.lib import scheduler
scheduler.start()

def send_emails(email_template,recipient_list,substitution_dict=None):
    """
    Gets an email template from demisauce and sends
    to recipient list using scheduler which runs in the background
    allowing this current request to continue processing
    """
    #print 'in send_emails 1=%s, 2=%s, 3=%s' % (email_template,recipient_list,substitution_dict)
    from demisauce.lib import mail
    from demisaucepy import pylons_helper, demisauce_ws_get
    import urllib
    
    #/api/email/html/your_slug_title_here?apikey=f3f5de7f8376daf29ce3232ca606904ff4adc929
    resource_id = urllib.quote_plus(email_template)
    emails = demisauce_ws_get('email',resource_id,format='xml')
    if emails and emails.success:
        t = emails.xml_node.email[0]
        from string import Template
        s = Template(t.template)
        template = s.substitute(substitution_dict)
        mail.send_mail_toeach((t.subject,
                template, '%s<%s>' % (t.from_name,t.from_email), recipient_list))
        log.debug('sent emails to %s' % recipient_list)
    elif not emails.success:
        log.debug('Invalid DS WS call')
        return 'invalid api key'



base_url = h.base_url

def rendertf(filename,vars=[]):
    """Render a Tempita File"""
    fp = open(config['buffet.template_options']['mako.directories'][0]+filename)
    tmpl = tempita.Template(fp.read())
    return tmpl.substitute(vars)

def sanitize(text):
    return libsanitize.Sanitize(text)

def redirect_wsave(*args, **kwargs):
    """
    allows redirect to a destination, but first saves alerts and current
    request messages to something that will still exist on that next
    request
    """
    h.messages_tosession()
    redirect_to(*args, **kwargs)

def print_timing(func):
    """prints how long method took
    from http://www.daniweb.com/code/snippet452.html
    """
    def wrapper(*arg):
        t2 = time.clock()
        res = func(*arg)
        t3 = time.clock()
        url = request.environ['PATH_INFO']
        method = request.environ['REQUEST_METHOD']
        log.debug('%s %s took %0.3fms  %s, %s' % (method,url, (t3-t2)*1000.0,t3,t2))
        return res
    
    return wrapper


class BaseController(WSGIController):
    requires_auth = False
    
    def start_session(self,user):
        if user:
            session['user'] = user
            site = user.site
            c.user = user
            session.save()
            log.debug('in base controller setting user ')
    
    def __before__(self):
        """
            request.cookies['userkey']
            session['current_user_person'] = user
        """
        # Authentication required?
        if self.requires_auth and 'user' not in session:
            # Remember where we came from so that the user can be sent there
            # after a successful login
            session['return_url'] = request.path_info
            session.save()
            return redirect_to(h.url_for(controller='account',action='signin'))
        
        c.form_errors = c.form_errors or {}
        c.user = None
        c.base_url = h.base_url()
        c.help_url = h.help_url()
        c.adminsite_slug = 'demisauce.org'
        if 'user' in session and type(session['user']) == Person:
            c.user = session['user']
            c.site_id = c.user.site_id
        elif 'userkey' in request.cookies:
            user = meta.DBSession.query(Person).filter_by(
                    user_uniqueid=request.cookies['userkey'].lower()).first()
            if user:
                c.user = user # per request user for comment system, not not authed
        else:
            pass
    
    @print_timing
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method the
        # request is routed to. This routing information is available in
        # environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            #log.debug('in base controller __call__ remove session' )
            if meta.DBSession:
                meta.DBSession.remove()
    

class SecureController(BaseController):
    requires_auth = True
    
class NeedsadminController(BaseController):
    requires_auth = True
    def __before__(self):
        BaseController.__before__(self)
        # Sys Admin Level Access Required
        if not c.user:
            return redirect_to(h.url_for(controller='account',action='signin'))
        if not c.user.isadmin:
            # Get Out Of Here
            return redirect_to(h.url_for(controller='home',action='index'))
        
    


# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']

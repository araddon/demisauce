import urllib, urllib2, logging
import openanything
from pylons import cache, config, request
import datetime
from demisaucepy import demisauce_ws_get
import pylons
from pylons.util import AttribSafeContextObj, ContextObj
from pylons.i18n import ugettext
from xmlnode import XMLNode
from demisaucepy import cfg


log = logging.getLogger(__name__)
    
def current_url():
    qs = ''
    if 'QUERY_STRING' in request.environ:
        qs = '?%s' % request.environ['QUERY_STRING']
    url = 'http://%s/%s%s' % (request.host,request.path_info,qs)
    
    return url

def route_url(includeaction=True):
    """ Returns the url minus id, so controller/action typically"""
    url = ''
    if 'controller' in request.environ['pylons.routes_dict']:
        url += '/%s' % request.environ['pylons.routes_dict']['controller']
    if includeaction and 'action' in request.environ['pylons.routes_dict']:
        url += '/%s' % request.environ['pylons.routes_dict']['action']
    return url

def help_url(includeaction=True):
    """Returns the Html for the page you are on"""
    url = '/api/script/cms/root/help%s' % route_url(includeaction)
    return url


def get_admin_permissions():
    """
    Returns a Boolean if current user has permission to add/edit cms items
    """
    if 'pylons.h' in config:
        try:
            if 'pylons.h' in cfg.CFG:
                dsadmin = getattr(cfg.CFG['pylons.h'], 'isdemisauce_admin')
                if dsadmin:
                    return cfg.CFG['pylons.h'].isdemisauce_admin()
        except AttributeError:
            pass
    return False

def demisauce_xmlnodes(**kwargs):
    #TODO:  implement a simpleinterface similar to declarative mapper
    #phphello = has_a(name='helloworld',app='phpdemo',lazy=True,local_key='id' )
    raise NotImplementedError
    

def remote_html(resource_id='',routes_dict=None,append_path=False,**kwargs):
    """
    Accepts a key of which content is desired
    
    Returns None if not available or not found
    """
    url = request.environ['PATH_INFO']
    if append_path and routes_dict != None: 
        resource_id += request.environ['pylons.routes_dict'][routes_dict]
    elif append_path and routes_dict == None:
        #resource_id += url
        resource_id += '/%s' % request.environ['pylons.routes_dict']['controller']
        resource_id += '/%s' % request.environ['pylons.routes_dict']['action']
    
    isadmin = get_admin_permissions()
    if isadmin:
        log.debug('isadmin user')
    item = pylons_demisauce_ws_get('cms',resource_id,isadmin=isadmin,format='html') or ''
    if item.success:
        return item.data
    elif isadmin:
        # show the admin links?
        return '<a href="%s/cms/add/%s?returnurl=%s">Add Item</a>' % (
                config['demisauce.url'], resource_id, urllib.quote_plus(current_url()))
    else:
        return ''
    

def email_template_get(resource_id='',**kwargs):
    """
    retrieves the xml web service template, and returns as XMLNode
    """
    node = pylons_demisauce_ws_get('email',resource_id,format='xml')
    return node


def pylons_demisauce_ws_get(method, resource_id='', format='html', isadmin=False, cachetime=0,**kwargs):
    """
    method
    resource_id (which piece of content)
    """
    def ws_get():
        return demisauce_ws_get(method,resource_id,format=format)
        
    mycache = cache.get_cache('demisauce.remotecontent')
    
    if cachetime == 0:
        if 'demisauce.cacheduration' in cfg.CFG:
            cachetime = int(cfg.CFG['demisauce.cacheduration'])
    # Get the value, this will create the cache copy the first time
    # and any time it expires (in seconds, so 3600 = one hour)
    myvalue = mycache.get_value('%s-%s-%s' % (method,resource_id,format), createfunc=ws_get,expiretime=cachetime)
    return myvalue


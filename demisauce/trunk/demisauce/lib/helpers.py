"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
import os, logging
from webhelpers import *
from pylons import c, config

import pylons
from pylons import cache, session, c
from demisaucepy.pylons_helper import *
import urllib, hashlib


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

def base_url():
    """
    Gets base/root url:  http://localhost:4950 or fqdn etc
    """
    return config['demisauce.url']

def current_url(includeaction=True):
    """ Returns the url minus id, so controller/action typically"""
    url = ''
    if 'controller' in request.environ['pylons.routes_dict']:
        url += '/%s' % request.environ['pylons.routes_dict']['controller']
    if includeaction and 'action' in request.environ['pylons.routes_dict']:
        url += '/%s' % request.environ['pylons.routes_dict']['action']
    return url
    
def is_current(matchlist,toreturn="current"):
    """
    Determines if current http request uri matches the passed in nav item
    """
    for match in matchlist:
        if match == None:
            if request.environ['PATH_INFO'] == '/':
                return toreturn
        elif request.environ['PATH_INFO'].find(match) >= 0:
            return toreturn
        elif match.find('=') > 0:
            ml = match.split('=')
            if ml[0] in request.params and request.params[ml[0]] == ml[1]:
                return toreturn
    return ""

def is_currentqs(matchlist,toreturn="current"):
    """
    Determines if current http request uri querhstring
    matches the passed in nav item
    """
    for match in matchlist:
        if match in request.params:
            return toreturn
    return ""

htmlCodes = [
    ['&', '&amp;'],
    ['<', '&lt;'],
    ['>', '&gt;'],
    ['"', '&quot;'],
]
htmlCodesReversed = htmlCodes[:]
htmlCodesReversed.reverse()

def html_encode(s, codes=htmlCodes):
    """ Returns the HTML encoded version of the given string. This is useful to
    display a plain ASCII text string on a web page."""
    for code in codes:
        s = s.replace(code[0], code[1])
    return s

def isdemisauce_admin():
    """
    Determines if current user is DemiSauce admin, and if so will show
    a link to Demisauce admin to add items that don't exist
    """
    if not c.user:
        return False
    elif c.user.id == 1:
        return True
    print 'not demisauce admin %s' % c.user.email
    return False

def tag_links(tags):
    """
    Converts a list of tags to a list of links
    """
    if tags == None: return ""
    return '  '.join(["<a href=\"/node/tag/%s\">%s</a>" % (tag,tag)  for tag in tags.split()])

def add_alert(msg):
    """
    Use this from controllers to add a system message
    """
    c.msg_alerts = c.msg_alerts or []
    c.msg_alerts.append(msg)

def messages_tosession():
    """
    moves all local messages to session for a redirect
    """
    msgs = []#[c.form_errors[k]  for k in c.form_errors.keys()]
    msgs += [x  for x in c.msg_errors]
    session['errors'] = msgs
    msgs = [x  for x in c.msg_alerts]
    session['messages'] = msgs
    session.save()

def add_error(msg):
    """
    Use this from controllers to add an error message
    """
    c.msg_errors = c.msg_errors or []
    c.msg_errors.append(msg)

def round_box(html_content):
    return """<div class="corner_box statusmsgboxrc tempmessage">
                <div class="corner_top"><div></div></div>
                   <div class="corner_content">
                      %s
                   </div>
                <div class="corner_bottom"><div></div></div>
             </div>""" % (html_content)

def error_box():
    if 'errors' in session:
        c.msg_errors = c.msg_errors or []
        c.msg_errors += session['errors'] 
        del(session['errors'])
        session.save()
        
    s = ''
    if (c.form_errors and len(c.form_errors) > 0) or \
        (c.msg_errors and len(c.msg_errors) > 0):
        s += '<img src="/images/dialog-error.png" class="ib"/>'
    if (c.form_errors and len(c.form_errors) > 0):
        s += 'There were errors on the form highlighted below'
    s += ''.join(["%s <br />" % (x)  for x in c.msg_errors])
    return (len(s) > 0 or '') and ("$.ds.humanMsg.displayMsg('%s');" % s)
    return (len(s) > 0 or '') and round_box(s)

def msg_box():
    if 'messages' in session:
        c.msg_alerts = c.msg_alerts or []
        c.msg_alerts += session['messages'] 
        del(session['messages'])
        session.save()
        
    s = '' + ''.join(["%s <br />" % (x)  for x in c.msg_alerts])
    return (len(s) > 0 or '') and ("$.ds.humanMsg.displayMsg('%s');" % s)
    return (len(s) > 0 or '') and round_box(s)


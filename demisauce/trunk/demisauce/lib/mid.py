"""Middleware for testing
"""
import logging, time, cgi
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, validate, rest
from pylons.i18n import _, ungettext, N_
from pylons.templating import render

log = logging.getLogger(__name__)

def dowork_after(func):
    """hopefully allows us to do work after response is returned """
    def wrapper(*arg):
        res = func(*arg)
        log.debug('logging after')
        return res
    return wrapper

class DSMiddleware(object):
    def __init__(self, wrap_app):
        log.debug('middleware init')
        self.wrap_app = wrap_app
    
    #@dowork_after
    def __call__(self, environ, start_response):
        log.debug('testing in middleware')
        return self.wrap_app(environ, start_response)
    



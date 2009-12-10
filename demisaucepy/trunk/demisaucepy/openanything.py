'''OpenAnything: a kind and thoughtful library for HTTP web services

This program is part of 'Dive Into Python', a free Python book for
experienced programmers.  Visit http://diveintopython.org/ for the
latest version.
'''

__author__ = 'Mark Pilgrim (mark@diveintopython.org)'
__version__ = '$Revision: 1.6 $'[11:-2]
__date__ = '$Date: 2004/04/16 21:16:24 $'
__copyright__ = 'Copyright (c) 2004 Mark Pilgrim'
__license__ = 'Python'

import urllib2, urlparse, gzip
import urllib, logging, os
from StringIO import StringIO

ISGAE = False
log = logging.getLogger(__name__)

try:
    from google.appengine.api import urlfetch
    if 'AUTH_DOMAIN' in os.environ and 'gmail.com' in os.environ['AUTH_DOMAIN']:
        log.info('seems to be google app engine')
        ISGAE = True
except ImportError:
    pass

USER_AGENT = 'OpenAnything/%s +http://diveintopython.org/http_web_services/' % __version__

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result
    
    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        return result
    

class DefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):
    def http_error_default(self, req, fp, code, msg, headers):
        result = urllib2.HTTPError(
            req.get_full_url(), code, msg, headers, fp)
        result.status = code
        return result
    
class GAEResponse(object):
    def __init__(self,gae_response,url=''):
        self.url = url
        self.status = gae_response.status_code
        self.gaer = gae_response
    
    def read(self):
        return self.gaer.content
    def close(self):
        pass
    

def openAnything(source, data={}, etag=None, lastmodified=None, agent=USER_AGENT,extra_headers={}):
    """    
    This function lets you define parsers that take any input source
    (URL, pathname to local or network file, or actual data as a string)
    and deal with it in a uniform manner.  Returned object 
    (except google app engine fetcher) has all the basic stdio 
    read methods (read, readline, readlines).
    Just .close() the object when you're done with it.
    
    if data is supplied (in a dictionary), it will be http POST'ed
    
    If the etag argument is supplied, it will be used as the value of an
    If-None-Match request header.
    
    If the lastmodified argument is supplied, it must be a formatted
    date/time string in GMT (as returned in the Last-Modified header of
    a previous request).  The formatted date/time will be used
    as the value of an If-Modified-Since request header.
    
    If the agent argument is supplied, it will be used as the value of a
    User-Agent request header.
    """
    if hasattr(source, 'read'):
        return source
    
    if urlparse.urlparse(source)[0] == 'http':
        # open URL with urllib2, or gae fetch
        log.debug('about to open %s, extra_headers=%s' % (source,extra_headers))
        if ISGAE:
            if data == None or data == {}:
                response = urlfetch.fetch(url=source,headers=extra_headers)
            else:
                response = urlfetch.fetch(url=source,payload=data,
                    method=POST,headers=extra_headers)
            return GAEResponse(response,url=source)
        else:
            if data == None or data == {}:
                request = urllib2.Request(source)
            else:
                request = urllib2.Request(source,urllib.urlencode(data))
            request.add_header('User-Agent', agent)
            if lastmodified:
                request.add_header('If-Modified-Since', lastmodified)
            if etag:
                request.add_header('If-None-Match', etag)
            for key in extra_headers:
                log.debug('adding header key=%s, val=%s' % (key,extra_headers[key]))
                request.add_header(key,extra_headers[key])
            request.add_header('Accept-encoding', 'gzip')
            opener = urllib2.build_opener(SmartRedirectHandler(), DefaultErrorHandler())
            return opener.open(request)
    


def fetch(source, data={}, etag=None, lastmodified=None, agent=USER_AGENT,extra_headers={}):
    '''Fetch data and metadata from a URL, file, stream, or string
    
    example::
        
        import demisaucepy as ds
        
        result = ds.openanything.fetch('http://www.google.com')
    '''
    result = {}
    f = openAnything(source, data, etag, lastmodified, agent,extra_headers=extra_headers)
    result['data'] = f.read()
    if hasattr(f, 'headers'):
        # save ETag, if the server sent one
        result['etag'] = f.headers.get('ETag')
        # save Last-Modified header, if the server sent one
        result['lastmodified'] = f.headers.get('Last-Modified')
        if f.headers.get('content-encoding') == 'gzip':
            # data came back gzip-compressed, decompress it
            result['data'] = gzip.GzipFile(fileobj=StringIO(result['data'])).read()
    if hasattr(f, 'url'):
        result['url'] = f.url
        result['status'] = 200
    if hasattr(f, 'status'):
        result['status'] = f.status
    f.close()
    return result
    

import os.path

import paste.fileapp
from pylons.middleware import error_document_template, media_path
from paste.deploy.converters import asbool
from demisauce.lib.base import *

class ErrorController(BaseController):
    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.
    """
    def documentxx(self):
        """Render the error document"""
        print 'in error.py controller'
        if asbool(config['debug']) and request.params.get('code', '') == '500':
            # we re in debug mode, return pylons handler
            return self.pylons_default()
        elif (request.environ['paste.recursive.old_path_info'] and
            request.environ['paste.recursive.old_path_info'][0].find('/api/') >= 0):
            print 'oldpath = %s' % request.environ['paste.recursive.old_path_info'][0]
            if request.environ['paste.recursive.old_path_info'][0].find('/api/xml/') >= 0:
                # special page for xml api
                response.headers['Content-Type'] = 'application/xhtml+xml'
                return "<?xml version=\"1.0\" encoding=\"utf-8\" ?>" + \
                        "<exception id=\"401\" code=\"%(code)s\">%(message)s</exception>" \
                     % {'code':request.params.get('code', ''), \
                        'message':request.params.get('message', '')}
            else:
                # special page for html api
                return """<html><head><title>Error %(code)s</title></head>
                    <body><h1>Error %(code)s</h1><p>%(message)s</p></body></html>
                    """ % {'code':request.params.get('code', ''), \
                        'message':request.params.get('message', '')}
            
        else:
            return render('/error.html')
            return self.pylons_default()
    
    def document(self):
        """Render the error document"""
        page = error_document_template % \
            dict(prefix=request.environ.get('SCRIPT_NAME', ''),
                 code=request.params.get('code', ''),
                 message=request.params.get('message', ''))
        return page
    
    def pylons_default(self):
        """Render the error document"""
        page = error_document_template % \
            dict(prefix=request.environ.get('SCRIPT_NAME', ''),
                 code=request.params.get('code', ''),
                 message=request.params.get('message', ''))
        return page
    
    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file(os.path.join(media_path, 'img', id))
    
    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file(os.path.join(media_path, 'style', id))
    
    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        fapp = paste.fileapp.FileApp(path)
        return fapp(request.environ, self.start_response)
    


import logging
from pylons import config
from demisauce.lib.base import *

import pickle
#from cStringIO import StringIO

log = logging.getLogger(__name__)

class EnvironmentController(SecureController):

    def index(self):
        import cgi
        import pprint
        c.testout += "<tr style=\"background:#cccccc;\" valign=\"top\"><td>Session</td><td></td></tr>\n"
        for x in session:
            c.testout += "<tr  valign=\"top\"><td>%s:</td><td>%s </td></tr>\n" % (x,session[x])
        #c.pretty_environ = cgi.escape(pprint.pformat(request.environ))
        c.testout += "<tr style=\"background:#cccccc;\" valign=\"top\"><td>Request.environ</td><td></td></tr>\n"
        c.testout += "<tr  valign=\"top\"><td>request.params:</td><td>%s</td></tr>\n" % (request.params)
        for x in request.environ:
            c.testout += "<tr  valign=\"top\"><td>%s:</td><td>%s</td></tr>\n" % (x,request.environ[x])
        #src = StringIO()
        #p = pickle.Pickler(g)
        c.testout += "<tr style=\"background:#cccccc;\" valign=\"top\"><td>Config</td><td></td></tr>"
        #for x in config:
        #    c.testout += "<tr  valign=\"top\"><td>%s:</td><td></td></tr>" % (x)
        for x in config:
            c.testout += "<tr  valign=\"top\"><td>%s:</td><td>  %s </td></tr>" % (x,config[x])

        return render('/environment.html')

import logging
from django import template
from django.template import resolve_variable
#from django.template import Variable
from demisaucepy.declarative import service_view
from demisaucepy import cfg
log = logging.getLogger(__name__)


class ViewResolverNode(template.Node):
    def __init__(self, service, view_string,format='view',app='demisauce'):
        self.view_string = str(view_string)
        self.service = service
        self.format = format
        self.app = app
    
    def render(self, context):
        html = service_view(self.service,self.view_string,format=self.format,app=self.app)
        return html
    
class UrlResolverNode(template.Node):
    def __init__(self, app):
        self.url = cfg.CFG['demisauce.url']
    
    def render(self, context):
        return self.url
    

def dsview(parser, token):
    try:
        service_tuple = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires two arguments, service, and view name" % token.contents.split()[0]
    if not (service_tuple[1][0] == service_tuple[1][-1] and service_tuple[1][0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % service_tuple[0]
    if len(service_tuple) < 3:
        raise template.TemplateSyntaxError, "%r tag requires two arguments, service, and view name" % token.contents.split()[0]
    tagname = service_tuple[0][1:-1]
    service = service_tuple[1][1:-1]
    view = service_tuple[2][1:-1]
    return ViewResolverNode(service, view)
    
    
def dsurl(parser, token):
    try:
        pass
        #url = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag doesnt use any arguments" % token.contents.split()[0]
    return UrlResolverNode('demisauce')


try:
    #this should fail if not inside the gae dev, or prod
    from google.appengine.ext import webapp as wa
    register = wa.template.create_template_register()
    log.debug('in gae version of demisauce tags, so django tags not being used')
    register.tag('dsview', dsview)
    register.tag('dsurl', dsurl)
except ImportError:
    log.debug('running django demisaucetags setup, no gae detected')
    register = template.Library()
    register.tag('dsview', dsview)
    register.tag('dsurl', dsurl)





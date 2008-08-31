from django import template
from django.template import resolve_variable
#from django.template import Variable
from demisaucepy.declarative import service_view


register = template.Library()

class ViewResolverNode(template.Node):
    def __init__(self, service, view_string):
        self.view_string = str(view_string)
        self.service = service
    
    def render(self, context):
        html = service_view(self.service,self.view_string)
        return html

def dsview(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, service, view_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires two arguments, service, and view name" % token.contents.split()[0]
    if not (view_string[0] == view_string[-1] and view_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name
    return ViewResolverNode(service[1:-1], view_string[1:-1])

register.tag('dsview', dsview)



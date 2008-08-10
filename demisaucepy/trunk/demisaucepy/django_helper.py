from django.db import models
from django.db.models.base import ModelBase
from demisaucepy.declarative import AggregatorMeta
from django.conf import settings
from django.template import Library, Node, resolve_variable, TemplateSyntaxError
"""
Example usage in html template:
   
   <script type="text/javascript" src="{{ current_url }}/js/jquery-1.2.6.pack.js"></script>
"""

def demisauce_vars(request):
    cur_url = '%s?%s' % (request.path, request.GET.urlencode())
    return {
        'demisauce_url': settings.DEMISAUCE_URL,
        'current_url': cur_url
    }


class ModelAggregatorMeta(ModelBase,AggregatorMeta): pass


class DjangoModel(models.Model):
    __metaclass__ = ModelAggregatorMeta

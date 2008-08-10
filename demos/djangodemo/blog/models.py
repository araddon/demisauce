from django.db import models
from django.db.models.base import ModelBase
from django.contrib import admin
from demisaucepy.django_helper import ModelAggregatorMeta
from demisaucepy.declarative import Aggregagtor, has_a, \
    has_many, aggregator_callable, AggregateView, AggregatorMeta


#class ModelAggregatorMeta(ModelBase,AggregatorMeta): pass


class Blog(models.Model):
    
    title = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.title
    

class Entry(models.Model):
    __metaclass__ = ModelAggregatorMeta
    blog = models.ForeignKey(Blog)
    title = models.CharField(max_length=255)
    pub_date = models.DateTimeField('date published')
    content = models.TextField()
    comments = has_many(name='comment',lazy=True,local_key='id' )
    def __unicode__(self):
        return self.title
    
    
admin.site.register(Blog)
admin.site.register(Entry)

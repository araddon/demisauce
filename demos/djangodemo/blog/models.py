from django.db import models
from django.db.models.base import ModelBase
from django.contrib import admin
from demisaucepy.django_helper import ModelAggregatorMeta
from demisaucepy.declarative import has_a, has_many, \
    AggregateView


class Entry(models.Model):
    __metaclass__ = ModelAggregatorMeta
    title = models.CharField(max_length=255)
    pub_date = models.DateTimeField('date published')
    content = models.TextField()
    comments = has_many(name='comment',lazy=True,local_key='id' )
    phphello = has_a(name='helloworld',app='phpdemo',lazy=True,local_key='id' )
    def __unicode__(self):
        return self.title
    

admin.site.register(Entry)

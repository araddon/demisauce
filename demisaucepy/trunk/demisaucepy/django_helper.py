from django.db import models
from django.db.models.base import ModelBase
from demisaucepy.declarative import AggregatorMeta


class ModelAggregatorMeta(ModelBase,AggregatorMeta): pass


class DjangoModel(models.Model):
    __metaclass__ = ModelAggregatorMeta

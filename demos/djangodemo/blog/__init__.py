from django.conf import settings
from demisaucepy import cfg


cfg.CFG['demisauce.apikey'] = settings.DEMISAUCE_APIKEY
cfg.CFG['demisauce.url'] = settings.DEMISAUCE_URL
cfg.CFG['demisauce.appname'] = settings.DEMISAUCE_APPNAME
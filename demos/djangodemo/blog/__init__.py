from django.conf import settings
from demisaucepy import cfg


cfg.CFG['demisauce_api_key'] = settings.DEMISAUCE_APIKEY
cfg.CFG['demisauce_url'] = settings.DEMISAUCE_URL
cfg.CFG['demisauce_appname'] = settings.DEMISAUCE_APPNAME
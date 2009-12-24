from django.conf import settings
import demisaucepy
from tornado.options import options


options.demisauce_api_key = settings.DEMISAUCE_APIKEY
options.demisauce_url = settings.DEMISAUCE_URL
options.demisauce_appname = settings.DEMISAUCE_APPNAME
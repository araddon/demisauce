#!/usr/bin/env python
import tornado.options
from tornado.options import define, options
import demisaucepy.options

__version__ = '0.1.1'


define("facebook_api_key", help="your Facebook application API key",
        default="1c9724431c6a5ebb2167b87862373776")
define("facebook_secret", help="your Facebook application secret",
        default="13c61611ccac41a95cbfe9a940b0afbd")
define("twitter_consumer_key", help="your Twitter application API key",
        default="7xjPzAjqtH5QqitEicaFqQ")
define("twitter_consumer_secret", help="your Twitter application secret",
        default="g9Wg0fDCcFN4IGtJ8PB9TYq5RiRMEPSfqZ3MkcPPl9Y")
define("base_url", default="http://localhost:4950", help="base fq url, no trailing slash to site")
define("debug",default=True,help="run in debug mode or not, if so auto-reloads",type=bool)
define("port", default=4950, help="run on the given port", type=int)

define("sqlalchemy_default_url", default=("mysql://root:demisauce@192.168.1.7/demisauce"))
define("sqlalchemy_default_echo", default=True, type=bool,help="run in echo mode")
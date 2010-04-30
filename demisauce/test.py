"""
-s means don't capture stdout, send to terminal
::
    python test.py --config=nose.cfg demisauce/tests/test_models.py:test_site -s
"""
import windmill
import nose
import logging
import os
import tornado
from tornado.options import options, define
import demisauce.appbase
import demisaucepy.options
from demisaucepy.cache import DummyCache, MemcacheCache


TEST_ROOT = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.realpath(TEST_ROOT + '/dev.conf' )
tornado.options.parse_command_line([0,"--config=%s" % config_file, '--logging=debug'])

# turn down Nose
nose_logger = logging.getLogger('nose')
nose_logger.setLevel(logging.ERROR)

memcache_cache = MemcacheCache(options.memcached_servers)

# Have one global connection to the DB across app
from demisauce import model
db = model.get_database(cache=memcache_cache)

nose.main()
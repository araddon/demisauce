"""
-s means don't capture stdout, send to terminal
::
    python test.py --verbosity=3 -s
    
    python test.py --config=nose.cfg
    
    python test.py tests/sanitize_test.py  --config=nose.cfg
    
    python test.py --with-coverage
    
    python test.py tests/sanitize_test.py  --config=nose.cfg --with-coverage
    
    python test.py tests/func_test.py  --config=nose.cfg -s
    python test.py tests/wm_test.py  --config=nose.cfg -s --wmbrowser firefox --wmtesturl http://localhost:8001
    
    
    
"""
import windmill
import nose
import os
import tornado
from tornado.options import options, define
import demisauce.appbase
import demisaucepy.options
from demisaucepy.cache import DummyCache, MemcacheCache


TEST_ROOT = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.realpath(TEST_ROOT + '/dev.conf' )
tornado.options.parse_command_line([0,"--config=%s" % config_file, '--logging=debug'])
memcache_cache = MemcacheCache(options.memcached_servers)

# Have one global connection to the DB across app
from demisauce import model
db = model.get_database(cache=memcache_cache)

nose.main()
import logging, os, sys
from unittest import TestCase
import string
import tornado
from tornado.options import options, define, enable_pretty_logging
import demisaucepy.options

TEST_ROOT = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.realpath(TEST_ROOT + '/../../../demisauce/dev.conf' )
tornado.options.parse_command_line([0,"--config=%s" % config_file, '--logging=debug'])
print("about to setup cache = %s" % options.demisauce_cache)
print("about to demisauce_api_key = %s" % options.demisauce_api_key)
from demisaucepy import cache_setup

cache_setup.load_cache(cachetype=options.demisauce_cache)


import demisaucepy


class TestDSBase(TestCase):
    """
    Test base class
    """
    def __init__(self, *args):
        self.url = options.demisauce_url
        TestCase.__init__(self, *args)

__all__ = ['TestDSBase']

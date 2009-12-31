"""
Testing framework for demisauce python api
"""
import logging
from unittest import TestCase
import string
import demisaucepy
import tornado
from tornado.options import options, define, enable_pretty_logging

def load_config():
    """load's config"""
    tornado.options.parse_command_line(["--config=../../demisauce.conf"])
    from demisaucepy import cache_setup
    cache_setup.load_cache(cachetype=options.demisauce_cache)
load_config()


class TestDSBase(TestCase):
    """
    Test base class
    """
    def __init__(self, *args):
        self.url = options.demisauce_url
        TestCase.__init__(self, *args)

__all__ = ['TestDSBase']

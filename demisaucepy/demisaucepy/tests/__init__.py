"""
Testing framework for demisauce python api
"""
import logging
from unittest import TestCase
import string
from demisaucepy import LoadConfig, cfg
import tornado
from tornado.options import options, define, enable_pretty_logging

def load_config():
    """load's config"""
    cfg.CFG = LoadConfig("test.ini")
    logging.getLogger().setLevel(getattr(logging, "ERROR"))
    #enable_pretty_logging()
    from demisaucepy import cache_setup
    logging.debug("setting up load_cache")
    cache_setup.load_cache(cachetype=cfg.CFG['demisauce_cache'])
load_config()


class TestDSBase(TestCase):
    """
    Test base class
    """
    def __init__(self, *args):
        #logging.debug("testDSBase.__Init__ cfg.CFG = %s" % cfg.CFG)
        self.cfg = cfg.CFG
        self.url = cfg.CFG['demisauce_url']
        TestCase.__init__(self, *args)

__all__ = ['TestDSBase']

"""
Testing framework for demisauce python api
"""
import logging
from unittest import TestCase
import string
from demisaucepy import *
from demisaucepy import cfg


def load_config():
    """load's config"""
    cfg.CFG = LoadConfig("test.ini")
    from demisaucepy import pylons_helper as h
    h.CFG = cfg.CFG
    print cfg.CFG

load_config()

class TestDSBase(TestCase):
    """
    Test base class
    """
    def __init__(self, *args):
        self.cfg = cfg.CFG
        self.url = cfg.CFG['demisauce.url']
        TestCase.__init__(self, *args)

__all__ = ['TestDSBase']

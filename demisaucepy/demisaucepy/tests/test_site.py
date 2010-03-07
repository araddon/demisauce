import logging
import json
from tornado.options import options
from demisaucepy import Site, jsonwrapper
from demisaucepy.tests import TestDSBase

log = logging.getLogger(__name__)

class TestSite(TestDSBase):
    def test_site_create(self):
        "test site creation"
        assert True == False
    


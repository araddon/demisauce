"""
This is the base content item
"""
import logging
import json
from tornado.options import options
from demisaucepy import Site, jsonwrapper
from demisaucepy.tests import TestDSBase

log = logging.getLogger(__name__)

class TestApi(TestDSBase):
    def test_site_create(self):
        "test site creation"
        response = demisauce_ws('email','welcome_to_demisauce',format='json')
        
        assert response.success == True
        assert response.json is not None
        assert len(response.json) == 1 # should return exactly one record
        emailjson = response.json[0]
        assert 'subject' in emailjson
        assert 'Demisauce' in emailjson['subject']
        print emailjson['template']
    


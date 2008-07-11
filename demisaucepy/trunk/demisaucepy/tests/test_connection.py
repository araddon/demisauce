"""
This is the simple test for connectivity
"""
from demisaucepy.tests import *
from demisaucepy import demisauce_ws, hash_email, \
    demisauce_ws_get



class TestConnectivityAndExistence(TestDSBase):
    """
    Test core connection to the demisauce server
    """
    def test_connection(self):
        """
        Test that Server is up, apikey works
        """
        assert self.cfg['demisauce.url'] == 'http://localhost:4951'
        item = demisauce_ws_get('connect','')
        assert item.success == True
        assert item.data
        # we should have a valid api key
        assert item.data.find('connected') >= 0
    

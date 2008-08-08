"""
Base test class for ensuring the demisaucepy/pylons_helper.py is working
"""
from pylonsdemo.tests import *
from demisaucepy import *
from demisaucepy import pylons_helper
from demisaucepy.pylons_helper import email_node_get
from pylons import config

class TestPylonsHelper(TestController):
    def test_pylons_helper(self):
        # connect to ds web services, only difference with this api
        # and the core one is it caches
        dsitem = email_node_get('welcome_to_demisauce')
        assert dsitem.success == True
        assert dsitem.data
        assert dsitem.xml_node
        emailnodes = [e for e in dsitem.xml_node]
        assert len(emailnodes) == 1
        email2 = dsitem.xml_node.email[0]
        assert email2
        assert email2.subject == 'welcome to demisauce'

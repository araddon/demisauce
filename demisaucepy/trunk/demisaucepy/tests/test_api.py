"""
This is the base content item
"""
from demisaucepy.tests import *
from demisaucepy import demisauce_ws_get
from demisaucepy.models import RemoteService


class TestApi(TestDSBase):
    def test_emailget(self):
        """
        Test the xml get capabilities of email
        """
        dsitem = demisauce_ws_get('email','welcome_to_demisauce',format='xml')
        assert dsitem.success == True
        assert dsitem.data
        assert dsitem.xml_node
        #print dsitem.data
        # this is really more of a test of xmlnode, should move it
        emailnodes = [e for e in dsitem.xml_node]
        assert len(emailnodes) == 1, 'ensure length of array of nodes is 1'
        for e in emailnodes:
            assert e.subject == 'Welcome To Demisauce', 'ensure suject for each node is what we want'
        email2 = dsitem.xml_node.email[0]
        assert email2
        assert email2.subject == 'Welcome To Demisauce', 'ensure we can 0 index the array and use directly'
        assert 'verify your account' in email2.template, 'ensure the template is populated'
        email = dsitem.xml_node.email  
        assert email
        assert email.subject == 'Welcome To Demisauce', 'ensure for 1 length arrays we can access xml node directly'
        
    def test_cmshtmlget(self):
        """
        Test the html get capabilities of cms
        """
        item = demisauce_ws_get('cms','blog',format='html')
        assert item.success == True
        assert item.data
        assert item.data.find('Demisauce Server') >= 0
        
    

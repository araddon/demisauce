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
        response = demisauce_ws_get('email','welcome_to_demisauce',format='xml')
        assert response.success == True
        #print response.data
        email = response.model
        #print response.xmlnode
        #print dir(response.xmlnode)
        #print len(response.xmlnode)
        assert response.model is not None
        assert len(response.xmlnode) == 1 # this means email = model
        #print dir(model)
        #print 'is model none?  %s' % (model == None)
        # this is really more of a test of xmlnode, should move it
        assert email.subject == 'Welcome To Demisauce', 'ensure suject for each node is what we want'
        assert email.key == 'welcome_to_demisauce'
        assert 'Welcome' in email.template
        
    def test_cmshtmlget(self):
        """
        Test the html get capabilities of cms
        """
        item = demisauce_ws_get('cms','blog',format='html')
        assert item.success == True
        assert item.data
        assert item.data.find('Demisauce Server') >= 0
        
    

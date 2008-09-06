"""
This is the base content item
"""
import logging
from demisaucepy.tests import *
from demisaucepy import demisauce_ws_get
from demisaucepy.models import RemoteService

log = logging.getLogger(__name__)

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
        
    
    def test_xmlproc(self):
        """
        Test via xmlrpc
        """
        from demisaucepy import cfg
        from demisaucepy.cache import cache
        from demisaucepy import demisauce_ws, hash_email, \
            ServiceDefinition, ServiceClient, RetrievalError, \
            UrlFormatter
        #from google.appengine.api import urlfetch
        
        sd = ServiceDefinition(
                name='wordpress',
                app_slug='wordpress'
            )
        sd.isdefined = False
        sd.method_url = None
        #.service_registry = None
        #self.api_key = api_key
        sd.base_url = "http://192.168.125.133/blog/xmlrpc.php"
        client = ServiceClient(service=sd)
        #client.extra_headers = self.extra_headers
        response = client.fetch_service(request="wp.getPages",data={})
        assert client.service.format == 'xmlrpc'
        
        assert response.model[0].wp_slug == 'demisauce-official-introduction'


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
    
    def test_xmlproc(self):
        """
        Test via xmlrpc
        """
        from demisaucepy import cfg
        from demisaucepy.cache import cache
        from demisaucepy import demisauce_ws, hash_email, ServiceClient, \
            ServiceDefinition, RetrievalError, args_substitute
        """{'wp_author': 'admin', 
            'userid': '1', 
            'excerpt': '', 
            'wp_page_parent_id': '0', 
            'mt_allow_comments': 1, 
            'text_more': '', 
            'custom_fields': [{'value': '1', 'id': '2', 'key': '_edit_last'}, {'value': '1232858127', 'id': '1', 'key': '_edit_lock'}], 
            'wp_author_id': '1', 
            'title': 'About', 
            'wp_password': '', 
            'wp_page_parent_title': '', 
            'page_id': '2', 
            'wp_slug': 'about', 'wp_page_order': '0', 
            'permaLink': 'http://192.168.0.106/blog/about/', 
            'description': 'This is an example of a <strong>WordPress</strong> page, you could edit this to put information about yourself or your site so readers know where you are coming from. You can create as many pages like this one or sub-pages as you like and manage all of your content inside of WordPress.', 'dateCreated': <DateTime '20090124T12:02:32' at 143cda0>, 'wp_author_display_name': 'admin', 'link': 'http://192.168.0.106/blog/about/', 'page_status': 'publish', 'categories': ['Uncategorized'], 'wp_page_template': 'default', 'mt_allow_pings': 1, 'date_created_gmt': <DateTime '20090124T19:02:32' at 143cfa8>}
        
        """
        sd = ServiceDefinition(
                name='wordpress',
                app_slug='wordpress'
            )
        sd.isdefined = False
        sd.method_url = None
        #.service_registry = None
        #self.api_key = api_key
        #sd.base_url = "http://192.168.0.106/blog/xmlrpc.php"
        client = ServiceClient(service=sd)
        #client.extra_headers = self.extra_headers
        response = client.fetch_service(request="2",data={'blog_id':'1','user':'admin','password':'admin'})
        page = response.model[0]
        assert client.service.format == 'xmlrpc'
        assert page.wp_author == 'admin'
        assert page.wp_slug == 'about'
        #print page.description


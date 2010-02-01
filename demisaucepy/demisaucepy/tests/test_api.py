"""
This is the base content item
"""
import logging
import json
from tornado.options import options
#import demisauce # force load of options?
from demisaucepy.tests import *
from demisaucepy import demisauce_ws_get, httpfetch
#from demisaucepy import RemoteService
from demisaucepy.cache import cache
from demisaucepy import demisauce_ws, Service, hash_email, ServiceClient, \
    ServiceDefinition, RetrievalError, args_substitute

log = logging.getLogger(__name__)

class TestApi(TestDSBase):
    def test_connection(self):
        "test base api connectivity, auth"
        """
        {u'from_name': u'Demisauce Admin', 
            u'template': u'Welcome to Demisauce;\n\nYour account has been enabled, and you can start using services on demisauce.\n\nTo verify your account you need to click and finish registering $link\n\nThank You\n\nDemisauce Team', 
            u'from_email': u'demisauce@demisauce.org', 
            u'to': None, 
            u'slug': u'welcome_to_demisauce', 
            u'reply_to': None, 
            u'id': 1, u'subject': 
            u'Welcome To Demisauce'}
        """
        response = demisauce_ws('email','welcome_to_demisauce',format='json')
        assert response.success == True
        assert response.json is not None
        assert len(response.json) == 1 # should return exactly one record
        emailjson = response.json[0]
        assert 'subject' in emailjson
        assert 'Demisauce' in emailjson['subject']
"""

    def test_emailsend(self):
        "test if we can send an email"
        from gearman import GearmanClient
        from gearman.task import Task
        gearman_client = GearmanClient(options.gearman_servers)
        #send emails
        jsondict = {
            'template_name':'thank_you_for_registering_with_demisauce',
            'emails':['araddon@yahoo.com'],
            'template_data':{
                'displayname':'Bob User',
                'title':'welcome',
                'email':'araddon@yahoo.com',
                'link':'http://www.demisauce.com/?fake=testing'
            }
        }
        num_sent = gearman_client.do_task(Task("email_send",json.dumps(jsondict), background=False))
        logging.debug("test emailsend num_sent = %s" % (num_sent))
        assert num_sent == '1'
    
    def test_email_native(self):
        "test if we can send an email by embedding entire message template"
        from gearman import GearmanClient
        from gearman.task import Task
        gearman_client = GearmanClient(options.gearman_servers)
        #send emails by passing the template
        jsondict = {
            'template':'This tests templating',
            'emails':['araddon@yahoo.com'],
            'template_data':{
                'displayname':'Bob User',
                'title':'welcome',
                'link':'http://www.demisauce.com/?fake=testing'
            }
        }
        #num_sent = gearman_client.do_task(Task("email_send",json.dumps(jsondict), background=False))
        #assert num_sent == '1'
        assert True == False
        #send emails by passing the message body
        jsondict = {
            'message':'This tests messaging, no template',
            'emails':['araddon@yahoo.com'],
        }
        #num_sent = gearman_client.do_task(Task("email_send",json.dumps(jsondict), background=False))
        #assert num_sent == '1'
        assert True == False
    
    def test_email_via_webhook(self):
        "Post an http web hook call to ds with request to send email"
        jsondict = {
            'template_name':'thank_you_for_registering_with_demisauce',
            'emails':['araddon@yahoo.com'],
            'template_data':{
                'displayname':'Bob User',
                'title':'welcome',
                'email':'araddon@yahoo.com',
                'link':'http://www.demisauce.com/?fake=testing'
            }
        }
        data = json.dumps(jsondict)
        url = "http://localhost:4950/api/email/thank_you_for_registering_with_demisauce/send.json?apikey=a95c21ee8e64cb5ff585b5f9b761b39d7cb9a202"
        response = httpfetch.fetch(url, data=data)
        assert response['status'] == 200
        assert 'data' in response
    

"""

def xmlproc(self):
    """
    Test via xmlrpc
    """
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


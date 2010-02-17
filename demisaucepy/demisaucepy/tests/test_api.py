"""
This is the base content item
"""
import logging
import json
import tornado
import tornado.httpclient
from tornado.options import options
from demisaucepy import demisauce_ws, Object, Activity, Email, Site
from demisaucepy import jsonwrapper
from demisaucepy.tests import TestDSBase

log = logging.getLogger(__name__)

class TestApi(TestDSBase):
    def test_connection(self):
        "test base api connectivity, auth"
        response = demisauce_ws('email','welcome_to_demisauce',format='json')
        
        assert response.success == True
        assert response.json is not None
        assert len(response.json) == 1 # should return exactly one record
        emailjson = response.json[0]
        assert 'subject' in emailjson
        assert 'Demisauce' in emailjson['subject']
    
    def test_remoteobject(self):
        'test remote object loads data'
        email = Email.GET('welcome_to_demisauce')
        assert email._response.success == True
        assert len(email) == 1
        assert 'Demisauce' in email.subject
        assert hasattr(email,'subject')
        
        email = Email.GET("not_an_existing_template")
        assert email is None
    
    def test_site(self):
        site_dict = {
            "name": "TESTING app", 
            "key": "x7456asdfasdf", 
            "email": "test@demisauce.org", 
            "slug": "unittesting",
            "base_url": "http://testing.demisauce.com",
            "enabled":"True",
            "this_is_extra":"this should go in extra json"
        }
        site = Site(site_dict)
        site.POST()
        assert site._response.success == True
        assert site._response.status == 201
        assert site.id > 0
        assert site.name == site_dict['name']
        assert site.extra_json['this_is_extra'] == site_dict['this_is_extra']
        #return
        # ok, now lets add different extra
        site2 = Site(id=site.id)
        assert site2.id == site.id
        site2.extra_json = {'more_extra':'testing'}
        site2.POST()
        assert site.id == site2.id
        assert site.name == site2.name
        assert site2.extra_json['this_is_extra'] == site_dict['this_is_extra']
        assert site2.extra_json['more_extra'] == 'testing'
        site.DELETE()
        site3 = Site.GET(site2.id)
        assert site3 is None
    
    def txest_extra_json(self):
        pass
    
    def test_json_body(self):
        'test json body posts work as well as args'
        http = tornado.httpclient.HTTPClient()
        url = '%s/api/email/not_an_existing_template3.json?apikey=%s'  % (options.demisauce_url,options.demisauce_api_key)
        email_dict = {
            "subject":"Welcome To Demisauce",
            "slug":"not_an_existing_template3",
            "from_email":"guest@demisauce.org",
            "from_name":"Demisauce Admin",
            "template": "Welcome to Demisauce;\n\n\nYour account has been enabled, and you can start using services on demisauce.\n\nTo verify your account you need to click and finish registering $link\n\nThank You\n\nDemisauce Team"
        }
        json_str = json.dumps(email_dict)
        email_result = http.fetch(url,method="POST",body=json_str)
        email = jsonwrapper(json.loads(email_result.body))
        assert email.subject == email_dict['subject']
        email = Email.GET(id='not_an_existing_template3',cache=False)
        assert email._response.success == True
        assert email._response.status == 200
        assert email.subject == email_dict['subject']
        svc = Email(id='not_an_existing_template3')
        svc.DELETE()
        email = Email.GET(id='not_an_existing_template3',cache=False)
        assert email is None
    

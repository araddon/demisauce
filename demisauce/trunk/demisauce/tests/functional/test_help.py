from demisauce.tests import *
from demisauce.tests.functional import BaseAdminController
from demisauce.model import help, site
import logging
log = logging.getLogger(__name__)

class TestHelpController(BaseAdminController):
    helpitem = None
    @classmethod
    def setupAll(cls):
        print 'in TestHelpPublicController.class_setup'
        h = help.Help(1,'sysadmin@demisauce.org')
        h.url = 'http://www.google.com'
        h.content = 'user comment goes here'
        h.save()
        TestHelpPublicController.helpitem = h
    
    def test_index(self):
        response = self.app.get(url_for(controller='helpadmin',action="index"))
        assert 'Feedback' in response
    
    def test_jshelpfile(self):
        # TODO: this is not using the site_key or site_slug and it should
        pass
        #response = self.app.get('/api/script/cms/root/help/dashboard/index')
        #print response.body
        #assert 'ds_help_output' in response
    
    def test_helpresponse(self):
        log.debug('/helpadmin/process/%s' % TestHelpPublicController.helpitem.id)
        print '/helpadmin/process/%s' % TestHelpPublicController.helpitem.id
        res = self.app.get('/helpadmin/process/%s' % TestHelpPublicController.helpitem.id)
        assert 'sysadmin@demisauce.org' in res, 'ticket from sysadmin@demisauce.org should be in page'
        assert 'dashboard' in res, 'ticket for url dashboard should be in page'
        res = self.app.post('/helpadmin/process', params={
            'help_id': TestHelpPublicController.helpitem.id , 
            'status':'10', 'publish' : '1', 'title': 'this is the response from nose',
            'response': 'this is response from admin'})
        assert 'Feedback' in res, 'make sure form was submitted successfully'
    

class TestHelpPublicController(TestController):
    def test_helpsubmit(self):
        res = self.app.get('/help/feedback')
        assert 'Feedback' in res
        res = self.app.post('/help/feedback/demisauce.org', params={'email': 
            'sysadmin@demisauce.org', 'content': 'testingfeedback','blog':'http://blog.com',
            'url':'http://localhost:4950/dashboard'})
        assert 'Thank You' in res, 'make sure form was submitted successfully'
    


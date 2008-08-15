from demisauce.tests import *
from demisauce.tests.functional import BaseAdminController
from demisauce.model import help, site, person
import logging
log = logging.getLogger(__name__)

class TestSecurityController(TestController):
    def test_personhasrole(self):
        admin = person.Person.by_email(1,'sysadmin@demisauce.org')
        assert admin != None
        assert admin.email == 'sysadmin@demisauce.org'
        assert admin.has_role('sysadmin') == True, 'should have sysadmin role'
        assert admin.has_role('fakerole') == False
        test_page = self.app.get('/email/testsecurity')
        assert '302 Found' in test_page, 'should get a 302 redirect to dashboard'
        assert not ('failed test security' in test_page)
    


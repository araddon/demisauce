from demisauce.tests import *
from demisauce import model
from pylons import config
from demisauce.model import init_model

class BaseAdminController(TestController):
    def setUp(self):
        #model.test_connect()
        print 'in base admin controller'
        res = self.app.post('/account/signin', params={'email': 'sysadmin@demisauce.org', 'password': 'admin'})
        assert 'dashboard' in res  # 302 redirect to dashboard




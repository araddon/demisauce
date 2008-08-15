from demisauce.tests import *
from demisauce.tests.functional import BaseAdminController
from demisauce.model import help, site, person, comment, \
    group
from pylons import config

class TestPersonGroupController(BaseAdminController):
    personitem = None
    groupitem = None
    @classmethod
    def setupAll(cls):
        print 'in TestPersonController.setupAll'
        p = person.Person(site_id=1,email='guest@demisauce.org',displayname='Demisauce Web',raw_password='admin')
        p.url = 'http://www.google.com'
        p.save()
        TestPersonGroupController.personitem = p
        g = group.Group(1)
        g.name = 'testing group creation setupall'
        newtogroup, newtosite = g.add_memberlist('afakeemail@demisauce.org')
        g.save()
        TestPersonGroupController.groupitem = g
    
    def test_index(self):
        response = self.app.get(url_for(controller='account',action="settings"))
        assert 'Your Personal Profile' in response
    
    def test_group_webcreate(self):
        response = self.app.get(url_for(controller='groupadmin',action="addedit"))
        assert 'Group' in response
        res = self.app.post('/groupadmin/addedit', params={
            'group_id':'0',
            'name':'name of new group',
            'members': 'guest@demisauce.org'})
        response = self.app.get(url_for(controller='groupadmin',action="index"))
        assert 'name of new group' in response
    
    def test_group_webservice(self):
        assert TestPersonGroupController.groupitem.id > 0
        url = url_for('/api/xml/group/%s' % (TestPersonGroupController.groupitem.id))
        print url
        response = self.app.get(url)
        print response
        assert 'testing group creation setupall' in response, 'should have xml of name of group'
        assert 'afakeemail@demisauce.org' in response, 'should have members list'
    

class TestPersonPublicController(TestController):
    def test_personsignup(self):
        res = self.app.get('/account/signup')
        assert 'Invitation' in res
        res = self.app.post('/user/interest', params={'email': 
            'signingup@demisauce.com'})
        assert 'redirected automatically' in res, 'make sure form was submitted successfully, if you get redirected it did'
    


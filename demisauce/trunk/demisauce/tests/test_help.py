"""
This is the testing for basic model CRUD
"""
import nose
from sqlalchemy.exceptions import *
from demisauce.tests import *
from demisauce import model
from demisauce.model import mapping, meta
from demisauce.model import cms, site, email, person, \
    help, group, poll, tag
from demisauce.model.help import helpstatus


class TestHelp(TestController):
    def test_help(self):
        h = help.Help(site_id=1,email='guest@demisauce.org')
        h.url = '/yourfolder/path'
        h.content = 'user comment goes here'
        h.save()
        h2 = help.Help.get(1,h.id)
        assert h.id == h2.id
        p = person.Person.get(1,1)
        hr = help.HelpResponse(help_id=h.id, site_id=1,person_id=p.id)
        hr.status = helpstatus['completed']
        assert hr.site_id == 1
        hr.url = h.url
        hr.title = 'title of response'
        hr.response = 'testing response'
        h.helpresponses.append(hr)
        # add tag portion
        tag1 = tag.Tag(tag='test',person=p)
        h.tags.append(tag1)
        
        h.save()
        assert tag1.id > 0
        tag2 = h.tags[0]
        assert tag2.value == 'test'
        assert tag2.assoc_id > 0
        assert tag2.association.type == 'help'
        assert hr.id > 0, 'should have saved'
        hr2 = help.HelpResponse.get(1,hr.id)
        assert hr2.response == 'testing response'
        assert hr2.url == '/yourfolder/path'
        h3 = help.Help.get(1,h.id)
        hr3 = h3.helpresponses[0]
        assert hr3.response == hr2.response
    

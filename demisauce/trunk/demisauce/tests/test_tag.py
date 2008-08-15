
import nose
from sqlalchemy.exceptions import *
from demisauce.tests import *
from demisauce import model
from demisauce.model import mapping, meta
from demisauce.model import cms, site, email, person, \
    help, group, poll, tag
from demisauce.model.help import helpstatus

class test_tag(TestController):
    def test_tagcrud(self):
        h = help.Help(site_id=1,email='guest@demisauce.org',
            url='/yourfolder/path',content = 'comment')
        h.save()
        person1 = person.Person.by_email(site_id=1,email='sysadmin@demisauce.org')
        assert person1.id > 0
        tag1 = tag.Tag(tag='test',person=person1)
        h.tags.append(tag1)
        tag1.save()
        assert tag1.id > 0
        assert tag1.value == 'test'
        assert tag1.assoc_id > 0
        assert tag1.association.type == 'help'
        tag1_get = tag.Tag.get(1,tag1.id)
        assert tag1_get.value == tag1.value
        #nose.tools.assert_raises(IntegrityError, p.save)
        #meta.DBSession.rollback()
        #meta.DBSession.close()
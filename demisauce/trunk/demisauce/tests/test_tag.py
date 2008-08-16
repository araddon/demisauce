
import nose
from pylons import config
from sqlalchemy.exceptions import *
from demisauce.tests import *
from demisauce import model
from demisauce.model import mapping, meta
from demisauce.model import cms, site, email, person, \
    help, group, poll, tag
from demisauce.model.help import helpstatus


class test_tag(TestController):
    def test_tagcrud(self):
        h1 = help.Help(site_id=1,email='guest@demisauce.org',
            url='/yourfolder/path',content = 'comment')
        h1.save()
        person1 = person.Person.by_email(site_id=1,email='sysadmin@demisauce.org')
        person2 = person.Person.by_email(site_id=1,email='admin@demisauce.org')
        assert person1.id > 0
        h2 = help.Help(site_id=1,email='admin@demisauce.org',
            url='/yourfolder/path',content = 'comment')
        h2.set_user_info(person2)
        h2.save()
        tag1 = tag.Tag(tag='test',person=person1)
        h1.tags.append(tag1)
        h1.tags.append(tag.Tag(tag='javascript',person=person1))
        h1.tags.append(tag.Tag(tag='python',person=person1))
        h1.tags.append(tag.Tag(tag='python',person=person2))
        tag1.save()
        h1.save()
        h2.tags.append(tag.Tag(tag='python',person=person2))
        h2.tags.append(tag.Tag(tag='javascript',person=person2))
        h2.tags.append(tag.Tag(tag='xmpp',person=person1))
        h2.save()
        assert tag1.id > 0
        assert tag1.value == 'test'
        assert tag1.assoc_id > 0
        assert tag1.association.type == 'help'
        tag1_get = tag.Tag.get(site_id=1,id=tag1.id)
        assert tag1_get.value == tag1.value
        tags = help.Help.tag_keys(site_id=1)
        assert 'javascript' in tags
        assert 'python' in tags
        assert len(tags) == 4
        tagct_list = tag.Tag.by_cloud(site_id=1,tag_type='help')
        assert len(tagct_list) == 4
        #meta.DBSession.close()
        h1get = help.Help.get(site_id=1,id=h1.id)
        h2get = help.Help.get(site_id=1,id=h2.id)
        meta.DBSession.refresh(h1get)
        meta.DBSession.refresh(h2get)
        assert h1get.content == 'comment'
        tag_keysh1 = [t.value for t in h1get.tags]
        tag_keysh2 = [t.value for t in h2get.tags]
        assert len(tag_keysh1) == 4
        assert 'test' in tag_keysh1
        assert len(tag_keysh2) == 3
        assert not 'test' in tag_keysh2
        meta.DBSession.refresh(person1)
        meta.DBSession.refresh(person2)
        tag_keys_p1 = [t.value for t in person1.tags]
        tag_keys_p2 = [t.value for t in person2.tags]
        assert len(tag_keys_p1) == 4
        assert len(tag_keys_p2) == 3
        assert 'xmpp' in tag_keys_p1
        

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

class TestModels(TestController):
    def test_person(self):
        email = person.Person.create_random_email()
        p = person.Person(site_id=1,email=email,
            displayname='Demisauce Web',raw_password='admin')
        p.url = 'http://www.google.com'
        p.save()
        p2 = person.Person.get(1,p.id)
        assert p2.email == email
        assert p.id == p2.id
        assert p2.id > 0
        # this should be a dupe
        p = person.Person(site_id=1,email='sysadmin@demisauce.org',
            displayname='Demisauce Web',raw_password='admin')
        p.url = 'http://www.google.com'
        nose.tools.assert_raises(IntegrityError, p.save)
        meta.DBSession.rollback()
        meta.DBSession.close()
    
    def test_email(self):
        e = email.Email(site_id=1,subject='My Test Email', from_email='email@demisauce.org',
                        template='this is the content to be sent')
        meta.DBSession.save(e)
        meta.DBSession.commit()
        meta.DBSession.flush()
        
        # Now, lets see if it was created
        e2 = meta.DBSession.query(email.Email).filter_by(subject='My Test Email').first()
        assert e.id == e2.id
        assert e.subject == e2.subject
        #assert e.key == e2.key
        #assert len(e.key) > 20  #decently long unique key
    
    def test_cmsitem(self):
        # Now we can create objects that exist in our ORM.
        c = cms.Cmsitem(TestModels.basesite.id, 'this is a title', 'the home page has content')
        meta.DBSession.save(c)
        meta.DBSession.commit()
        meta.DBSession.flush()

        # Now, lets see if it was created
        #c2 = meta.DBSession.query(cms.Cmsitem).filter_by(title='homepage').first()
        c2 = cms.get_by_title('this is a title')
        print c2.title
        #print c2.key
        print 'c.id = %s,  c2.id = %s ' % (c.id, c2.id)
        assert c.id == c2.id
        assert c.title == c2.title
        assert c.content == c2.content
        #assert c2.id == 1
    
    def test_site(self):
        s = site.Site(name='New Website on Demi', email='mail@mail.com')
        s.save()
        s2 = meta.DBSession.query(site.Site).filter_by(name='New Website on Demi').first()
        assert s.id == s2.id
        assert s.name == s2.name
        assert s2.name == 'New Website on Demi'
        assert s.key == s2.key
        assert len(s.key) > 20  #decently long unique key
    
    def test_group(self):
        """
        Test to ensure we can create groups, add users to groups
        update groups, etc
        """
        g = group.Group(1,'My Group Name')
        g.save()
        meta.DBSession.flush()
        assert g.id > 0
        # Now, lets see if it was created
        g2 = group.Group.get(1,g.id)
        assert g2.id == g.id
        assert g2.site_id == 1
        assert g2.name == 'My Group Name'
        assert g.name == g2.name
        
        # test group membership
        p = person.Person.get(1,1)
        p2 = person.Person.get(1,2)
        assert p.id > 0
        assert p2.id > 0
        assert len(g.members) == 0
        g.members.append(p)
        g.members.append(p2)
        g.name = 'Updated Group Name'
        g.save()
        meta.DBSession.flush()
        g3 = group.Group.get(1,g.id)
        assert g3.name == 'Updated Group Name', 'ensure you can edit/change values'
        assert len(g3.members) == 2
    
    def test_poll(self):
        p = poll.Poll(site_id=1,name='test poll',description='poll description')
        p.key = 'test-poll'
        p.save()
        meta.DBSession.flush()
        p2 = poll.Poll.get(1,p.id)
        assert p.id == p2.id
        assert p.name == p2.name
        assert p2.name == 'test poll'
        
        q = poll.Question(question="why is chocolate good?",type='radiowother')
        p.questions.append(q)
        o = poll.QuestionOption(option="because its sweet!")
        q.options.append(o)
        o2 = poll.QuestionOption(option="because its bitter!")
        q.options.append(o2)
        o3 = poll.QuestionOption(option="Other")
        o3.type = 'other'
        q.options.append(o3)
        p.save()
        p3 = poll.Poll.get(1,p.id)
        assert len(p3.questions) == 1
        assert p3.questions[0].question == 'why is chocolate good?'
        assert p3.questions[0].type == 'radiowother'
        assert len(p3.questions[0].options) == 3
        assert p3.questions[0].options[0].option == 'because its sweet!'
        assert p3.questions[0].options[1].option == 'because its bitter!'
        responder = person.Person.by_email(1,'admin@demisauce.org')
        assert responder > 0
        response = poll.PollResponse(person_id=responder.id)
        response.answers.append(poll.PollAnswer(question_id=q.id,option_id=o.id))
        p3.responses.append(response)
        p3.save()
        assert len(p3.responses) == 1
        assert p3.responses[0].person_id == responder.id
        responder2 = person.Person.by_email(1,'sysadmin@demisauce.org')
        assert responder2 > 0
        response2 = poll.PollResponse(person_id=responder2.id)
        response2.answers.append(poll.PollAnswer(question_id=q.id,option_id=o3.id,other='text answer'))
        p3.responses.append(response2)
        p3.save()
        p4 = poll.Poll.saget(p3.id)
        assert len(p3.responses) == 2
        assert p4.responses[1].person_id == responder2.id
        assert p4.responses[1].answers[0].other == 'text answer'
    


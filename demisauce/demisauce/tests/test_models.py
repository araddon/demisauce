"""
This is the testing for basic model CRUD
"""
import nose, logging
from sqlalchemy.exceptions import *
from demisauce.tests import *
from demisauce import model
from demisauce.model import mapping, meta
from demisauce.model import site, template, user
from demisauce.model.version import Version
from demisauce.model import actions

log = logging.getLogger('demisauce')

actions.add_action('testing_webhook',bg=True)

sites, users, groups, versions = [], [], [], []
def cleanup():
    global sites, users, groups
    #persons = xrange(446,449)
    #sites = [446,447,448]
    #groups = xrange(11,39)
    for sid in sites:
        s = site.Site.saget(sid)
        if s:
            s.delete()
    for pid in users:
        p = user.Person.saget(pid)
        if p:
            p.delete()
    for vid in versions:
        v = Version.saget(vid)
        if v:
            v.delete()

def setup():
    print("in module setup")
    global users, sites, groups, versions
    users = []
    #versions = [v.id for v in meta.DBSession.query(Version).filter_by(object_type="site",object_id=1).all()]
    cleanup()

def teardown():
    print("in module teardown")
    cleanup()

def test_person():
    "test user/person object"
    global users
    email = user.Person.create_random_email()
    p = user.Person(site_id=1,email=email,raw_password='admin',
        displayname='Demisauce Web',url = 'http://www.google.com')
    p.save()
    user_id = p.id
    users.append(p.id)
    assert p.id > 0
    p2 = user.Person.get(1,p.id)
    assert p2.email == email
    assert p.id == p2.id
    assert p.displayname == p2.displayname
    p2.add_attribute('betauser',True,object_type='segment',
            encoding='str',category='segment')
    p2.save()
    p3 = user.Person.get(1,p.id)
    assert p3.has_attribute('betauser')
    assert p3.is_authenticated('wrongpwd') == False
    assert p3.is_authenticated('admin') == True
    # make sure user attribute is only related to that user
    pn = user.Person.get(1,1)
    assert pn.has_attribute('betauser') == False
    
    # this should be a dupe
    p = user.Person(site_id=1,email=email,
        displayname='Demisauce Web',raw_password='admin')
    p.url = 'http://www.google.com'
    nose.tools.assert_raises(IntegrityError, p.save)
    meta.DBSession.rollback()
    meta.DBSession.close()
    # test cache
    pc = user.Person.get_cache(user_id)
    assert pc._is_cache == True
    assert hasattr(pc,'attributes')
    assert len([attr for attr in pc.attributes]) == 1
    pc = user.Person.get_cache(user_id)

def test_email():
    e = template.Template(site_id=1,subject='My Test Email', from_email='email@demisauce.org',
                    template='this is the content to be sent')
    e.save()
    meta.DBSession.flush()
    
    # Now, lets see if it was created
    e2 = meta.DBSession.query(template.Template).filter_by(subject='My Test Email').first()
    assert e.id == e2.id
    assert e.subject == e2.subject
    #assert e.key == e2.key
    #assert len(e.key) > 20  #decently long unique key

def test_site():
    'test site creation, config vals, etc'
    global sites
    s = site.Site.saget(1)
    assert s.is_new == False
    s = site.Site(name='New Website on Demi', email='mail@mail.com')
    s.save()
    assert s.id > 0
    assert s.is_new == True
    sites.append(s.id)
    log.debug("about to query when should hit init on load")
    s2 = meta.DBSession.query(site.Site).filter_by(name='New Website on Demi').first()
    assert s.id == s2.id
    assert s.name == s2.name
    assert s.slug == 'new-website-on-demi'
    assert s2.name == 'New Website on Demi'
    assert s.key == s2.key
    assert len(s.key) > 20  #decently long unique key
    # add settings/attributes
    s.add_attribute('mailchimp_apikey','mailchimpapikey',category='config')
    s.save()
    log.debug("about to call is_new %s" % s.is_new)
    s_id = s.id
    meta.DBSession.close()
    meta.DBSession()
    s = site.Site.saget(s_id)
    assert s.is_new == False
    assert s.has_attribute('mailchimp_apikey')
    attr = s.get_attribute('mailchimp_apikey')
    assert attr.value == 'mailchimpapikey'
    assert attr.object_id == s.id
    assert attr.object_type == 'site'
    
    sc = site.Site.get_cache(s.id)
    assert sc.id == s.id, 'compare cache vs real'
    assert sc.name == s.name
    s.delete()
    s3 = site.Site.saget(s.id)
    assert s3 == None, 'Should have deleted item'

def test_versioning():
    'test versioning'
    global versions
    # now lets try versioning
    s = site.Site.saget(1)
    assert s.name == 'demisauce'
    u = user.Person.saget(1)
    s.name = 'demisauce2'
    v1 = Version.create_version(s,u,expunge=True)
    assert v1.version == 0
    versions.append(v1.id)
    meta.DBSession.close()
    meta.DBSession()
    # Test that the session get() does NOT get the version with 'demisauce2'
    s = site.Site.saget(1)
    u = user.Person.saget(1)
    assert s.name == 'demisauce'
    s.name = 'demisauce3'
    v2 = Version.create_version(s,u,expunge=True)
    versions.append(v2.id)
    v_id = v2.id
    assert v2.object_id == 1
    assert v2.object_type == 'site'
    
    s2 = site.Site.saget(1)
    v2a = s2.version_latest
    v2b = Version.saget(v_id)
    assert v2a is v2b
    assert v2b.id == v2a.id, "Version from version_latest should match db"
    assert v2b.version == 1
    s = v2b.use_version(site.Site)
    s.save()
    assert s.name == 'demisauce3'
    s.name = 'demisauce'
    s.save()


def test_actions():
    'test actions'
    d = {'site_id':1,'echo':'Testing42'}
    actions.do_action('testing_webhook',**d)

def test_group():
    """
    Test to ensure we can create groups, add users to groups
    update groups, etc
    """
    g = user.Group(site_id=1,name='My Group Name')
    g.save()
    meta.DBSession.flush()
    assert g.id > 0
    # Now, lets see if it was created
    g2 = user.Group.get(1,g.id)
    assert g2.id == g.id
    assert g2.site_id == 1
    assert g2.name == 'My Group Name'
    assert g.name == g2.name
    
    # test group membership
    p = user.Person.get(1,1)
    p2 = user.Person.get(1,2)
    assert p.id > 0
    assert p2.id > 0
    #assert len(g.members) == 0
    g.members.append(p)
    g.members.append(p2)
    g.name = 'Updated Group Name'
    g.save()
    meta.DBSession.flush()
    g3 = user.Group.get(1,g.id)
    assert g3.name == 'Updated Group Name', 'ensure you can edit/change values'
    assert len(g3.members) == 2
    

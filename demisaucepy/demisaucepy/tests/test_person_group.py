import json, hashlib, random, logging
from demisaucepy.tests import *
from demisaucepy import demisauce_ws, hash_email, objectwrapper
from demisaucepy import DSUser, DSGroup

log = logging.getLogger("dspy.tests")

persons = []
groups = []

def setup():
    print("in module setup")
    global persons, groups
    #persons = xrange(504,512)
    #persons = [516]
    #groups = xrange(11,39)
    for pid in persons:
        userd = DSUser(id=pid)
        userd.DELETE()
    for gid in groups:
        groupd = DSGroup(id=gid)
        groupd.DELETE()
    persons = []
    groups = []

def teardown():
    print("in module teardown")
    global persons, groups
    #persons = xrange(312,314)
    #persons = [314]
    #groups = xrange(1,9)
    for pid in persons:
        userd = DSUser(id=pid)
        userd.DELETE()
    for gid in groups:
        groupd = DSGroup(id=gid)
        groupd.DELETE()

def create_random_email(domain='@demisauce.org'):
    """
    create a random email for testing
    accepts a @demisauce.org domain argument optionally
    """
    return '%s%s' % (hashlib.md5(str(random.random())).hexdigest(),domain)

def test_crud():
    'test deletion of person'
    email = create_random_email()
    person_data = {
        'email':email,
        'displayname':'library testing user',
        'url':'http://testingurls.com',
        'authn':'local',
        'foreign_id': 515,
        'attributes':[{'name':'FollowNotification','value':'all','category':'notification'}],
        'extra_json':{
            'segment1':'value1',
            'age':99
        }
    }
    user = DSUser(person_data)
    user.POST()
    assert user._response.status == 201
    user = DSUser.GET(user.id)
    assert user._response.success
    assert user._response.status == 200
    assert user.id > 0
    assert user.foreign_id == 515
    assert user.email == email
    assert user.displayname == 'library testing user'
    attr = user.attributes[0]
    assert attr.name == 'FollowNotification'
    assert attr.value == 'all'
    assert user.authn == 'local'
    assert user.extra_json.age == 99
    # make an edit
    user.displayname = 'library testing user v2'
    user.auth_source = "google"
    user.attributes.append({'name':'notify_weekly','value':'all','category':'notification'})
    user.POST()
    user2 = DSUser.GET(user.id)
    assert user.id == user2.id
    assert user2.displayname == 'library testing user v2'
    assert len(user2.attributes) == 2
    attr2 = user2.attributes[1]
    assert attr.name == 'notify_weekly' or attr.name == 'FollowNotification'
    assert attr.category == 'notification'
    assert attr.encoding == 'str'
    user.attributes = [{'name':'notify_weekly2','value':'all','category':'notification'}]
    user.POST()
    assert len(user.attributes) == 3
    userd = DSUser(id=user.id)
    userd.DELETE()
    assert userd._response.status == 204
    print('user_id in delete = %s' % user.id)
    user3 = DSUser.GET(user.id)
    assert user3 is None

def test_attributes():
    "test creation, update, deletion of attributes"
    dsuser2 = DSUser({'email':create_random_email(),'displayname':'attributes_user2'})
    assert dsuser2.attributes == None
    dsuser2.attributes = []
    dsuser2.attributes.append({'name':'name2','value':False})
    assert len(dsuser2.attributes) == 1
    dsuser2.POST()
    assert len(dsuser2.attributes) == 1
    assert dsuser2.attributes[0].name == 'name2'
    dsuser2.bool_setattr('notify_updates',True,'notifications')
    assert dsuser2.attributes[0].name == 'notify_updates' or dsuser2.attributes[1].name == 'notify_updates'
    #log.debug(dsuser2.to_form_data())
    assert dsuser2 != None
    dsuser2.DELETE()
    
    person_data = {
        'email':create_random_email(),
        'displayname':'attributes_user',
        'attributes':[{'name':'notify_follows','value':'all','category':'notification'}]
    }
    dsuser = DSUser(person_data)
    dsuser.POST()
    assert len(dsuser.attributes) == 1
    assert dsuser.attributes[0].name == 'notify_follows'
    
    dsuser.attributes = [{'name':'notify_weekly','value':'all','category':'notification'}]
    dsuser.POST()
    assert len(dsuser.attributes) == 2
    assert dsuser.has_attribute('notify_follows') == True
    assert dsuser.has_attribute('notify_weekly') == True
    # now make sure we can delete attributes
    dsuser.bool_setattr('notify_follows',False,'notifications')
    dsuser.POST()
    assert len(dsuser.attributes) == 1
    assert dsuser.has_attribute('notify_follows') == False
    assert dsuser.has_attribute('notify_weekly') == True
    dsuser.bool_setattr('notify_updates',True,'notifications')
    dsuser.bool_setattr('notify_follows',True,'notifications')
    dsuser.bool_setattr('notify_privatemsg',True,'notifications')
    dsuser.bool_setattr('notify_availability',False,'notifications')
    dsuser.bool_setattr('notify_weekly',False,'notifications')
    dsuser.bool_setattr('notify_locifood',False,'notifications')
    dsuser.POST()
    assert len(dsuser.attributes) == 3
    user_id = dsuser.id
    dsuser.DELETE()

def test_extra_json():
    'test that extra json gets made'
    user = DSUser({
        'email':create_random_email(),
        'displayname':'library testing user',
        'url':'http://testingurls.com',
        'authn':'local',
        'extra_json':{
            'segment1':'value1',
            'age':99
        },
        'an_extra_key':'aaron'
    })
    user.POST()
    assert user.id > 0
    user = DSUser.GET(user.id)
    assert user._response.success
    assert user.extra_json.age == 99
    assert user.an_extra_key == 'aaron'
    user.DELETE()
    user = DSUser.GET(1)
    assert user.extra_json == None
    user.POST()
    user = DSUser.GET(1)
    assert user.extra_json == None

def test_change_email():
    'since hashedemail is our key, if it changes we need to change'
    email = create_random_email()
    person_data = {
        'email':email,
        'displayname':'library testing user',
        'url':'http://testingurls.com',
        'authn':'local',
        'foreign_id':345
    }
    hashed_email = hash_email(email)
    user = DSUser(person_data)
    user.POST()
    assert user._response.success == True
    assert user.email == email
    assert isinstance(user.id,int)
    assert user.id > 0
    user_id = user.id
    uuid = user.user_uniqueid
    new_email = create_random_email()
    user.email = new_email
    user.POST(action='change_email',data={'email':new_email})
    assert user.id == user_id
    assert user.user_uniqueid == uuid
    assert user.displayname == person_data['displayname']
    assert user.email == new_email
    user.DELETE()
    assert user._response.status == 204

def test_group():
    """test creation of groups remotely, and update"""
    group_data = {
        'emails':['11ghty65@demisauce.org','abc12589@demisauce.org'],
        'name':'group added by web service',
        'extra_json':{
            'mailchimp_listid':99
        },
    }
    group = DSGroup(group_data)
    group.POST()
    assert group._response.success == True
    assert group.extra_json.mailchimp_listid == 99
    assert group.extra_json.emails == None
    assert group.mailchimp_listid == 99
    user = DSUser.GET('11ghty65@demisauce.org',cache=False)
    assert user.email == '11ghty65@demisauce.org'
    assert user.id > 0
    user.DELETE()
    user = DSUser.GET('abc12589@demisauce.org',cache=False)
    user.DELETE()
    group.DELETE()
    


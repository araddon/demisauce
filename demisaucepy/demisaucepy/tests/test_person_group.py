import json, hashlib, random
from demisaucepy.tests import *
from demisaucepy import demisauce_ws, hash_email, jsonwrapper
#from demisaucepy.models import Person
from demisaucepy import DSUser

def create_random_email(domain='@demisauce.org'):
    """
    create a random email for testing
    accepts a @demisauce.org domain argument optionally
    """
    return '%s%s' % (hashlib.md5(str(random.random())).hexdigest(),
        domain)

class test_person_group_api(TestDSBase):
    
    def test_delete_person(self):
        'test deletion of person'
        person_data = {
            'email':create_random_email(),
            'displayname':'library testing user',
            'url':'http://testingurls.com',
            'authn':'local',
            'foreign_id': 515,
            'extra_json':{
                'segment1':'value1',
                'age':'99'
            }
        }
        user = DSUser(person_data)
        user.POST()
        assert user._response.success
        assert user.id > 0
        assert user.foreign_id == 515
        user2 = DSUser.GET(user.id)
        assert user.id == user2.id
        
        userd = DSUser(id=user.id)
        userd.DELETE()
        user3 = DSUser.GET(user.id)
        assert user3 is None
    
    def test_extra_json(self):
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
        assert user._response.success
        assert user.extra_json.age == 99
        assert user.an_extra_key == 'aaron'
        user.DELETE()
        
    
    def test_change_email(self):
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
        response = demisauce_ws('person',hashed_email,'add',data=person_data,cache=False)
        assert response.success == True
        user = jsonwrapper(response.json[0])
        assert user.email == email
        assert user.id > 0
        new_email = create_random_email()
        response = demisauce_ws("person",hashed_email,'change_email',data={'email':new_email})
        user2 = jsonwrapper(response.json[0])
        assert user.id == user2.id
        assert user.user_uniqueid == user.user_uniqueid
        assert user.displayname == user.displayname
        assert user.email != user2.email
        assert user2.email == new_email
        assert user2.hashedemail == hash_email(new_email)
        response = demisauce_ws('person',user2.hashedemail,http_method="DELETE")
        print(response.status)
        assert response.status == 204
    
    def txest_person(self):
        """
        Test the json get capabilities of person/user account system
        Gets/Posts 
        """
        email = create_random_email()
        
        person_data = {
            'email':email,
            'displayname':'library testing user',
            'url':'http://testingurls.com',
            'authn':'local',
            'foreign_id': 515,
            'extra_json':{
                'segment1':'value1',
                'age':99
            }
        }
        hashed_email = hash_email(email)
        dsitem = demisauce_ws('person',hashed_email,data=person_data,cache=False)
        assert dsitem.success == True
        #print dsitem.json
        #print("Type = %s  len=%s" % (type(dsitem.json), len(dsitem.json)))
        plist = jsonwrapper(dsitem.json)
        #plist = [pl for pl in dsitem.json]
        assert len(plist) == 1, 'ensure one person added'
        p = plist[0]
        assert p != None, 'p should not be none'
        assert p.id > 0, 'userid should be returned'
        assert p.hashedemail == hashed_email
        assert p.email == email
        assert p.displayname == 'library testing user'
        assert p.authn == 'local'
        assert p.extra_json.age == 99
        person_data = {
            'email':email,
            'displayname':'library UPDATE',
            'url':'http://www.google.com',
            'authn':'google'
        }
        dsitem2 = demisauce_ws('person',hashed_email,data=person_data,format='json',cache=False)
        assert dsitem2.success == True
        assert len(dsitem2.json) == 1, 'ensure one person added'
        p2 = jsonwrapper(dsitem2.json[0])
        assert p2.displayname == 'library UPDATE', 'p2.displayname should have been updated'
        assert p2.id == p.id, 'userid should be same as other'
        assert p2.authn == 'google'
        response = demisauce_ws('person',hashed_email,http_method="DELETE")
        print(response.status)
        assert response.status == 204
    
    def txest_group_add_update(self):
        """test creation of groups remotely, and update"""
        group_data = {
            'email_list':'impossiblynonexistent@demisauce.org',
            'name':'group added by web service',
            'authn':'local'
        }
        assert True == True
    


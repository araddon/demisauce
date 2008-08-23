import nose
from sqlalchemy.exceptions import *
from demisauce.tests import *
from demisauce import model
from demisauce.model import mapping, meta
from demisauce.model import cms, site, email, person, \
    help, group, poll, tag
from demisauce.model.help import helpstatus
import simplejson

class test_loads(TestController):
    def test_loadjson(self):
        h = help.Help(site_id=1,email='guest@demisauce.org',
            url='/yourfolder/path',content = 'comment')
        h.save()
        person1 = person.Person.by_email(1,'sysadmin@demisauce.org')
        assert person1.email == 'sysadmin@demisauce.org'
        print '\nabout to print json'
        person_json = person1.to_json(indents=2)
        assert '"email": "sysadmin@demisauce.org"' in person_json
        print person_json
        person_list = model.ModelBase.from_json(person_json)
        person2 = person_list[0]
        assert person2.email == 'sysadmin@demisauce.org'
        assert person2.hashedemail == person1.hashedemail
        assert person2.displayname == person1.displayname
        assert person1.id == person2.id
        person2.save()
        assert person2.id == person1.id
        
        # test the loads from string
        person_list = model.ModelBase.from_json('''{
          "class": "demisauce.model.person.Person", 
          "data": [{
            "authn": "local", 
            "datetime_created": 1218721711.0, 
            "displayname": "sysadmin@demisauce.org", 
            "email": "sysadmin@demisauce.org", 
            "foreign_id": 0, 
            "hashed_password": "700318ec455f08e5f5f88f2a054e3962ae62acae", 
            "hashedemail": "0c0342d8eb446cd7743c3f750ea3174f", 
            "isadmin": true, 
            "issysadmin": true, 
            "last_login": null, 
            "random_salt": "f50e8031291ec23", 
            "url": "http:\/\/yourapp.wordpress.com", 
            "user_uniqueid": "423c919970fd8bacd1311acad2db8e17ec0c7bd5", 
            "verified": true, 
            "waitinglist": 0
          }]
        }''')
        assert type(person_list) == list
        person3 = person_list[0]
        person3.save()
        assert person3.email == 'sysadmin@demisauce.org'
        assert person3.id != person1.id
        assert person3.issysadmin == True
        assert person3.hashedemail == '0c0342d8eb446cd7743c3f750ea3174f'
        assert person3.user_uniqueid == '423c919970fd8bacd1311acad2db8e17ec0c7bd5'
    

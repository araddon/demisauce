"""
This is the base tests for creating/reading user data remotely
"""
from demisaucepy.tests import *
from demisaucepy import demisauce_ws, hash_email, \
    Person

class test_person_group_api(TestDSBase):
    
    def test_person(self):
        """
        Test the xml get capabilities of person/user account system
        as well as read's
        """
        email = Person.create_random_email()
        
        person_data = {
            'email':email,
            'displayname':'library testing user',
            'url':'http://testingurls.com',
            'authn':'local'
        }
        hashed_email = hash_email(email)
        dsitem = demisauce_ws('person',hashed_email,data=person_data,format='xml')
        assert dsitem.success == True
        plist = [pl for pl in dsitem.xml_node]
        assert len(plist) == 1, 'ensure length of array of nodes is 1'
        p = dsitem.xml_node.person
        assert p != None, 'p should not be none'
        assert p.id > 0, 'userid should be returned'
        assert p.hashedemail == hashed_email
        assert p.email == email
        assert p.displayname == 'library testing user'
        assert p.authn == 'local'
        person_data = {
            'email':email,
            'displayname':'library UPDATE',
            'url':'http://www.google.com',
            'authn':'google'
        }
        dsitem2 = demisauce_ws('person',hashed_email,data=person_data,format='xml')
        assert dsitem2.success == True
        p2 = dsitem2.xml_node.person
        assert p2.displayname == 'library UPDATE', 'p2.displayname should have been updated'
        assert p2.id == p.id, 'userid should be same as other'
        assert p2.authn == 'google'
        
    
    def test_group_add_update(self):
        """test creation of groups remotely, and update"""
        group_data = {
            'email_list':'impossiblynonexistent@demisauce.org',
            'name':'group added by web service',
            'authn':'local'
        }
        assert True == True


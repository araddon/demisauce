"""
This is the base tests for creating/reading user data remotely
"""
from demisaucepy.tests import *
from demisaucepy import demisauce_ws, hash_email, \
    Poll, Person

class test_poll_api(TestDSBase):
    
    def test_poll(self):
        """
        Test the xml get capabilities of poll
        
        """
        pollname = Person.create_random_email()
        p = Poll.by_name('test poll')
        assert p != None
        assert p.name == 'test poll'
        assert p.questions != None
        assert len(p.questions) > 0
        
    


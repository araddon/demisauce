"""
This is the base tests for creating/reading user data remotely
"""
from demisaucepy.tests import *
from demisaucepy import demisauce_ws, hash_email
from demisaucepy.models import Poll, Person

class test_poll_api(TestDSBase):
    
    def test_poll(self):
        """
        Test the xml get capabilities of poll
        
        """
        pollname = Person.create_random_email()
        p = Poll.by_name('what-should-the-new-features-be')
        #print p._xml
        assert p != None
        assert 'features' in p.name
        assert p.questions != None
        assert len(p.questions) > 0
        
    


import nose

from demisauce.tests import *
from demisauce import lib


class TestBase(TestController):
    def test_lib(self):
        assert 'aarons-good-stuff' == lib.slugify("aaron's good&*^ 89 stuff"), 'should replace bad stuff'
        
    

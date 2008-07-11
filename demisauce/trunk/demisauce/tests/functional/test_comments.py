from demisauce.tests import *

class TestCommentsController(TestController):
    def test_index(self):
        response = self.app.get(url_for(controller='home'))
        assert 'Demisauce' in response




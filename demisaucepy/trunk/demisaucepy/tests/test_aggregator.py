"""
This is the simple test for connectivity
"""
from demisaucepy.tests import *
from demisaucepy import demisauce_ws, hash_email, \
    demisauce_ws_get
from demisaucepy.models import Comment, Person as DemisaucePerson
from demisaucepy.declarative import Aggregagtor, has_a, \
    has_many, aggregator_callable, AggregateView


class AthletePerson(object):
    def __init__(self, arg):
        super(AthletePerson, self).__init__()
        self.arg = arg
    

AggregatorCallableCustomInheritanceTest = aggregator_callable(AthletePerson)

class Person(Aggregagtor):
    """
    Demo person class, showing direct inheritance implementation
    of Demisauce Aggregate Functions
    """
    personext = has_a('person',lazy=True,local_key='hashed_email')
    comments = has_many('comment',lazy=True,local_key='id')
    def __init__(self, displayname, email):
        super(Person, self).__init__()
        self.id = 145
        self.displayname = displayname
        self.email = email
        self.hashed_email = hash_email(email)
    

class SpecialAthlete(AggregatorCallableCustomInheritanceTest):
    def __init__(self, arg):
        super(SpecialAthlete, self).__init__()
        self.arg = arg
    


class test_aggregator(TestDSBase):
    """
    Test aggregation
    """
    def test_aggregator_hasa(self):
        p = Person('aaron','sysadmin@demisauce.org')
        assert type(p.personext) != None
        assert p.personext.model.email == 'sysadmin@demisauce.org'
        assert p.comments.model != None
        assert p.comments.view != None
        assert 'Comments' in p.comments.views.summary
        print '%s' % p.comments.views
        #TODO writes tests for aggregate view
        #views = AggregateView(p.comments,['summary','detail'])



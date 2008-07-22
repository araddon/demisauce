"""
This is the simple test for connectivity
"""
from demisaucepy.tests import *
from demisaucepy import demisauce_ws, hash_email, \
    demisauce_ws_get, Comment, Person as DemisaucePerson
from demisaucepy.declarative import Aggregagtor, has_a, \
    has_many, aggregator_callable


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
    comments = has_many('comment',lazy=True)
    def __init__(self, displayname, email):
        super(Person, self).__init__()
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
        p = Person('aaron','admin@demisauce.org')
        assert type(p.personext) != None
        assert p.personext.email == 'admin@demisauce.org'
    



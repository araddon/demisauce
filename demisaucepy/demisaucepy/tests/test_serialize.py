import logging, json, re, urllib
import tornado
import tornado.httpclient
from tornado.options import options
from demisaucepy import Object, Activity, Email, Site, DSUser
from demisaucepy.serializer import JsonSerializer, AvroSchemaSerializer, \
    get_schema
    
log = logging.getLogger("dspy.tests")

def setup():
    pass

def teardown():
    pass

site_dict = {
    "name": "TESTING app", 
    "key": "x7456asdfasdf", 
    "email": "test@demisauce.org", 
    "slug": "unittesting",
    "base_url": "http://testing.demisauce.com",
    "enabled":True,
    "this_is_extra":"this should go in extra json",
    "this_isa_list":['email2@demisauce.org','email3@demisauce.org']
}
site_list = [{
        "name": "TESTING app 2", 
        "key": "x7456asdfasdf", 
        "email": "test@demisauce.org", 
        "slug": "unittesting",
        "base_url": "http://testing.demisauce.com",
        "enabled":True,
        "this_is_extra":"this should go in extra json",
        "this_isa_list":['email2@demisauce.org','email3@demisauce.org']
    },{
        "name": "TESTING app 3", 
        "key": "x7456asdfasdf", 
        "email": "test@demisauce.org", 
        "slug": "unittesting",
        "base_url": "http://testing.demisauce.com",
        "enabled":True,
        "this_is_extra":"this should go in extra json",
        "this_isa_list":['email2@demisauce.org','email3@demisauce.org']
}]
def test_wrapper():
    site = Site(site_dict)
    sited = site.to_python()
    
def test_json():
    'test json round trips'
    site = Site(site_dict) # default serializer = jsonserializer
    assert site.name == site_dict['name']
    assert type(site.this_isa_list) == list
    assert'email2@demisauce.org' in site.this_isa_list
    assert site.enabled == True
    site = Site(site_list) # default serializer = jsonserializer
    assert len(site) == 2
    site1 = site[0]
    assert site1.name == site_list[0]['name']

def test_avro():
    "test avro serializer"
    Site.serializer = AvroSchemaSerializer(Site.avroschema) # change default 
    site = Site(site_dict)
    #print ("\nsite = %s, site_dict = %s" % (site,site_dict))
    avrosite = site.to_format()
    site = Site(avrosite)
    #print avrosite
    assert site.name == site_dict['name']
    print("type of this_isa_list = %s" % type(site.this_isa_list))
    assert type(site.this_isa_list) == list
    assert'email2@demisauce.org' in site.this_isa_list
    assert site.enabled == True
    # now try by passing in serializer
    site = Site(avrosite,serializer=Site.serializer)
    assert site.name == site_dict['name']
    assert type(site.this_isa_list) == list
    assert'email2@demisauce.org' in site.this_isa_list
    assert site.enabled == True

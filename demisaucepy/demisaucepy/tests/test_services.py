import logging
import json
from tornado.options import options
from demisaucepy.tests import *
from demisaucepy import demisauce_ws_get, httpfetch, Service

from demisaucepy.cache import cache


log = logging.getLogger(__name__)

class TestServices(TestDSBase):
    def test_api_base(self):
        'test base RemoteObjects, etc'
        svc = Service.GET(id=1000000000)
        assert svc is None
        svc = Service.GET(1)
        assert svc._response.status == 200
        # test user assuming a single entity returned
        assert svc.key == 'service'
        assert hasattr(svc,'key')
        assert svc.app.name == 'demisauce'
        # test user assuming more than one or unknown
        s = svc[0]
        assert s.key == 'service'
        assert s.app.name == 'demisauce'
        svcs = Service.GET("list")
        assert len(svcs) > 3, 'should have retrieved at least 3 services'
        return
    
    def test_service_api(self):
        "tests creation of services"
        service_data = {
            'name':'library testing service',
            'format':'json',
            'app_id':1,
            'owner_id':1,
            'method_url':'/api/testing/{key}.json?apikey={api_key}',
            'cache_time': 900
        }
        svc = Service(service_data)
        svc.POST()
        assert svc._response.success == True
        assert svc._response.status == 201
        assert isinstance(svc.id,int)
        assert len(svc) == 1, 'ensure one service added'
        assert svc.id > 0, 'service id should be returned'
        # reget from api
        svc = Service.GET(svc.id)
        assert svc.name == service_data['name']
        assert svc.format == service_data['format']
        # test updates
        #svc.name = 'updated name'
        svc.PUT({'name':'updated name'})
        #log.debug(svc._response.json)
        assert svc._response.success 
        assert svc.name == 'updated name'
        # Needs to update cache on PUT/POST 
        svc2 = Service.GET(svc.id)
        assert svc2 is not None
        
        assert svc2.name == 'updated name'
        assert svc._response.status == 201
        svc2.DELETE()
        svc3 = Service.GET(svc2.id)
        assert svc3 is None,'should not get result if deleted'
    




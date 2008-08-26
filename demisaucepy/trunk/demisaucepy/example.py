'''
Example consumer.
'''
import httplib
import time
from demisaucepy import cfg, ServiceDefinition, ServiceResponse, \
    ServiceTransportBase, GaeServiceTransport, HttpServiceTransport, \
    OAuthServiceTransport, ServiceClientBase, ServiceClient



def run_example():
    cfg.CFG['demisauce.url'] = 'http://localhost:4951'
    cfg.CFG['demisauce.apikey'] = 'a95c21ee8e64cb5ff585b5f9b761b39d7cb9a202'
    # setup
    print '** Demisaucepy Service Example**'
    service = ServiceDefinition(
        method='service',
        format='xml',
        app='demisauce'
    )
    print 'service %s:%s get' % (service.app, service.method)
    client = ServiceClient(service=service)
    response = client.fetch_service(request='demisauce/comment')# service definition for demisauce services
    """{
    'name': 'Comment Html Service', 
    'url': '/comment', 
    'description': 'Comment html and form ', 
    'base_url': 'http://localhost:4950', 
    'authn': 'demisauce', 
    'key': 'comment', 
    'id': '2', 
    'elelmentText': ['Comment Html Service', 'http://localhost:4950', 'demisauce', '/comment', 'Comment html and form ']}
    """
    mod = response.model
    print mod.base_url
    print mod.name
    print mod.description
    print mod.authn
    if mod.url_format == 'None':
        print "dang!   'None!"
    else:
        print 'crap'
    client2 = ServiceClient(service=service,transport=GaeServiceTransport())
    #client2.authorize()
    #client2.fetch_service()



if __name__ == '__main__':
    run_example()
    print 'Done.'
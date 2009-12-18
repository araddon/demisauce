"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    #map.connect('admin/:action/:id', controller='admin')
    map.connect('/', controller='home', action='index')
    map.connect('user/{action}/{id}', controller='account')
    #map.connect('cms/:key/:id', controller='cms', action='index')
    map.connect('cms/add/*key', controller='cms', action='add')
    map.connect('api/{format}/{action}/{id}', controller='api')
    map.connect('c/*key', controller='viewer', action='index')
    map.connect('kb/{key}/{id}', controller='viewer', action='viewer')
    map.connect('helpadmin/{action}/{id}/*other', controller='helpadmin')
    #map.connect('cms/get/:key/:id', controller='cms', action='index')
    # CUSTOM ROUTES HERE
    #map.connect(':controller/:action/:id')
    map.connect('{controller}/{action}/{id}')
    map.connect('*url', controller='template', action='view')
    
    #map.resource('message', 'messages')
    

    return map

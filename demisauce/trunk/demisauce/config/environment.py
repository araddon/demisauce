"""Pylons environment configuration"""
import os
from paste.deploy.converters import asbool
from sqlalchemy import engine_from_config
from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from pylons import config
from sqlalchemy import engine_from_config

import demisauce.lib.app_globals as app_globals
import demisauce.lib.helpers
from demisauce.config.routing import make_map
from demisauce.model import init_model

#from jinja2 import Environment, PackageLoader

has_amqp = False
try:
    import amqplib.client_0_8 as amqp
    has_amqp = True
except ImportError:
    pass

def load_engines(config,engines):
    # could be a comprehension but was a bit to long
    li = []
    for eng in engines.split(','):
        li.append(engine_from_config(config,eng,echo=asbool(config[eng + 'echo'])))
    return li

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])
    
    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='demisauce', paths=paths)
    
    config['routes.map'] = make_map()
    config['pylons.app_globals'] = app_globals.Globals()
    
    config['pylons.h'] = demisauce.lib.helpers
    
    if 'sqlalchemy.readengines' in config:
        config['pylons.app_globals'].sa_readengines = load_engines(config,config['sqlalchemy.readengines'])
        config['pylons.app_globals'].sa_masterengine = engine_from_config(config,
                'sqlalchemy.master.', echo=asbool(config['sqlalchemy.master.echo']))
        config['pylons.app_globals'].sa_readengines.append(config['pylons.app_globals'].sa_masterengine)
    else:
        #engine = engine_from_config(config, 'sqlalchemy.')
        engine = engine_from_config(config,
                        'sqlalchemy.default.', 
                        echo=asbool(config['sqlalchemy.default.echo']))
        init_model(engine)
        config['pylons.app_globals'].sa_engine = engine
        
    # Create the Jinja2 Environment
    config['pylons.app_globals'].jinja2_env = Environment(loader=ChoiceLoader(
            [FileSystemLoader(path) for path in paths['templates']]))
    # Jinja2's unable to request c's attributes without strict_c
    config['pylons.strict_c'] = True
    
    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)
    
    from demisauce.lib import dsconfig
    dsconfig.after_app_load()

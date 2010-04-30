import time, json, datetime, logging, sys, traceback, urllib
from datetime import datetime, date
import random, hashlib, string, re, urllib2
from tornado import escape
from tornado.options import define, options
import tornado.httpclient
from sqlalchemy import engine, orm
from sqlalchemy.sql import and_, or_, not_, func, select, text
from sqlalchemy.orm import mapper, relation, class_mapper, synonym, dynamic_loader
from sqlalchemy.orm import scoped_session, sessionmaker, join, eagerload
try:
    from gearman import GearmanClient
    from gearman.task import Task
except:
    from gearman import libgearman

#import twitter
#from demisauce.lib import bitly, publish
from demisauce import model
from demisauce.model import mapping
from demisauce.model import user, site
from demisaucepy.cache import DummyCache, MemcacheCache

log = logging.getLogger("demisauce")
db = None
actions = {} # global list of actions

gearman_client = GearmanClient(options.gearman_servers)

def send_email(name,user,data):
    jsondict = {
        'template_name':name,
        'emails':[user.email],
        'template_data':data,
        'apikey':options.demisauce_api_key
    }
    data = json.dumps(jsondict)
    url = "%s/api/email/%s/send.json?apikey=%s" % (options.demisauce_url,name,options.demisauce_api_key)
    gearman_client = GearmanClient(options.gearman_servers)
    gearman_client.do_task(Task("email_send",data, background=True))

def add_action(action,func=None,bg=False):
    """This adds a func to be called when action is called from do_action.   
    If func is none, then it is assumed that there is a subscriber configured 
    through site.settings that will be listening::
    
        add_action('webhook_testing',bg=True) # check for subscriber
    """
    global actions
    if action in actions:
        actorlist = actions[action]
        actorlist.append((bg,func))
        actions[action] = actorlist
    else:
        actions[action] = [(bg,func)]

def do_action(action,**kwargs):
    """triggers an action, checks if there are any listeners previously defined
    in add_action and runs those first. If the action called here is defined as
    run in background (defined in add_action) it will send to Gearman.  
    Requires site_id if is a plugin::
    
        do_action("new_user",{'site_id':1,'name':'bob'})
    """
    global actions
    if action in actions:
        actorlist = actions[action]
        for bg,func in actorlist:
            if bg:
                jsond = {'action':str(func.__name__) if func else action}
                for k in kwargs.keys():
                    if isinstance(kwargs[k],(str,unicode,int,long,list)):
                        jsond.update({k:kwargs[k]})
                    else:
                        log.debug('not adding %s type=%s' % (k,type(kwargs[k])))
                do_bg(jsond)
            else:
                func(**kwargs)

def do_action_bg(job_object):
    "deserializes info from gearman, finds action and processes"
    try: 
        global db
        if not db:
            # Have one global connection to the DB across app
            log.debug("in actions db get bg")
            memcache_cache = MemcacheCache(options.memcached_servers)
            db = model.get_database(cache=memcache_cache)
        db.session()
        g = globals()
        args = json.loads(job_object.arg)
        log.debug('in do_action_bg %s' % args)
        if 'action' in args and g.has_key(args['action']):
            log.debug('calling action = %s for args=%s' % (args['action'],args))
            g[args['action']](args)
        elif 'action' in args:
            log.debug('calling action 2 = %s for args=%s' % (args['action'],args))
            check_subscribers(args)
        else:
            log.error('whoops, that didnt work %s' % (args))
        db.session.close()
    except:
        logging.error("Error in gearman task do_action_bg:  %s" % traceback.print_exc())
        return -1

def do_bg(kwargs):
    log.debug('sending to bg %s' % kwargs)
    global gearman_client
    gearman_client.do_task(Task("demisauce_do_action_bg",json.dumps(kwargs), background=True))


def func_template(jsond):
    try: 
        u = user.Person.saget(jsond['user_id'])
        if u:
            log.debug("found user %s" % (u))
    except:
        logging.error("Error in gearman task activity_update_bg:  %s" % traceback.print_exc())
        return -1

def check_subscribers(args):
    """Checks if any subscribers, requires site_id in args"""
    try: 
        log.debug('in check_subscribers %s' % (args))
        if 'site_id' in args and 'action' in args:
            if args['action'].find('_user') > 0 and 'user_id' in args:
                o = user.Person.saget(args['user_id'])
                args.update({'user':o.to_dict_api()})
            
            s = site.Site.get_cache(args['site_id'],reload=False)
            hook = s.get_attribute(args['action'])
            if hook and hook.category == 'event' and hook.event_type == 'gearman':
                global gearman_client
                log.debug('found a gearman pub/sub hook = %s requires=%s' % (hook.value,hook.requires))
                if hook.requires and isinstance(hook.requires,(str,unicode)):
                    requires = json.loads(hook.requires)
                    for req in requires:
                        r = s.get_attribute(req)
                        if r:
                            args.update({r.name:r.value})
                log.debug('calling task args=%s' % args)
                gearman_client.do_task(Task(hook.value,json.dumps(args), background=True))
            elif hook and hook.category == 'event' and hook.event_type == 'webhook':
                http = tornado.httpclient.HTTPClient()
                log.debug("webhook calling url = %s" % (hook.value))
                res = http.fetch(hook.value,method="POST",body=json.dumps(args))
                log.debug("webhook resut = %s" % res.body)
        else:
            log.error("wtf, no site_id? %s" % (args))
    except:
        logging.error("Error in gearman task activity_update_bg:  %s" % traceback.print_exc())
        return -1


add_action('new_user',check_subscribers,bg=True)


def register_workers(worker):
    log.debug('registering demisauce_do_action_bg')
    worker.register_function("demisauce_do_action_bg", do_action_bg)


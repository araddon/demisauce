import tornado
import sys, traceback
from tornado.options import options
import os, logging, functools, urllib, urllib2
from functools import wraps
import re, datetime, random, string, time
import base64
import json
from demisaucepy import httpfetch

from gearman import GearmanClient
from gearman.task import Task


def stash_file(base64file,filename=None,gearman_client=None,args={}):
    """Accepts file handle from http upload, stashes, creates gearman worker"""
    new_file = ''.join([random.choice(string.letters + string.digits) for i in range(15)])
    if filename == None:
        extension = ".jpg"
    else:
        extension = re.search('\.\w+',filename).group()
    new_path = '%s/%s' % (random.choice(string.ascii_lowercase),random.choice(string.ascii_lowercase)) # two folders
    relative_path_wfile = '%s/%s' % (new_path,new_file)
    #local_path_wfile = '%s/%s%s' % (path,new_file,extension)
    
    if not gearman_client:
        gearman_client = GearmanClient(options.gearman_servers)
    json_data = {
        'file':new_file,
        'args':args,
        'extension':extension,
        'path':new_path,
        'path_w_file':relative_path_wfile,
        'url':'%sstatic/upload/%s%s' % (options.base_url,relative_path_wfile,extension),
        'image':base64file
    }
    gearman_client.do_task(Task("image_resize",json.dumps(json_data), background=True))
    return relative_path_wfile
import tornado
import sys, traceback
from tornado.options import options
import os, logging, functools, urllib, urllib2
from functools import wraps
import re, datetime, random, string, time
import base64
import json
from demisaucepy import httpfetch

from gearman import GearmanClient, GearmanWorker
from gearman.task import Task

try:
    from PIL import Image
except ImportError, err:
    print("NO PIL image processor")


log = logging.getLogger(__name__)

def job_in(fn):
    """ Decorates worker functions by calling them with a job's arguments """
    @wraps(fn)
    def new(job):
        # do something with the job object
        return fn(job.arg)
    return new

def json_in(fn):
    """ Decorates a function that may be called with a
        JSON-formatted string but expects a python object """
    @wraps(fn)
    def new(arg):
        # convert the args in JSON to a python object
        arg = json.loads(arg)
        return fn(arg)
    return new



def image_resize(job_object):
    """Resize Images Gearman Job"""
    try:
        job = json.loads(job_object.arg)
        base64_file = job['image']
        args = job['args'] if 'args' in job else {}
        del job['image']
        logging.info(job)
        
        def write_file(local_path,filename,file_b64):
            logging.debug("about to save to " + "%s/%s" % (local_path,filename))
            if not os.path.exists(local_path): os.makedirs(local_path)
            image_file = base64.b64decode(file_b64)
            local_file = open("%s/%s" % (local_path,filename), "w")
            local_file.write(image_file)
            local_file.close()
        
        def download_file(url,local_path,filename):
            print "downloading " + url
            f = urllib2.urlopen(urllib2.Request(url))
            print "about to save to " + "%s/%s" % (local_path,filename)
            if not os.path.exists(local_path): os.makedirs(local_path)
            # Open our local file for writing
            local_file = open("%s/%s" % (local_path,filename), "w")
            local_file.write(f.read())
            local_file.close()
        
        local_path = '%s/upload/%s' % (options.asset_root,job['path'])
        local_path_wfile = '%s/%s%s' % (local_path,job['file'],job['extension'])
        filename = '%s%s' % (job['file'],job['extension'])
        #download_file(job['url'],local_path,filename)
        write_file(local_path,filename,base64_file)
        
        def resize_and_save(local_file,new_file,maxsize=None,maxh=None,maxw=None,crop=None):
            """Resize the image and save"""
            logging.debug("maxsize=%s, crop=%s" % (maxsize,crop))
            img = Image.open(local_file)
            width,height = img.size
            width,height = float(width), float(height)
            ratio = float(1)
            if crop is not None:
                size = float(maxsize)
                if width <= height and width > size:
                    ratio = size/width
                elif height < width and height > size:
                    ratio = size/height
                else: 
                    ratio = 1 # too small
            elif maxsize:
                size = float(maxsize)
                if width >= height and width > size:
                    ratio = size/width
                elif height > width and height > size:
                    ratio = size/height
                else: 
                    ratio = 1 # too small
            elif maxh:
                size = maxh
                if height > size:
                    ratio = size/height
                else:
                    # too small
                    ratio = 1
            elif maxw:
                size = maxw
                if width > size:
                    ratio = size/width
                else:
                    # too small
                    ratio = 1
            else:
                raise Exception("must specify max width, OR max size")
            
            height = int(height*ratio)
            width = int(width*ratio)
            print("new ratio = %s:  size(x,y) = %s,%s" % (ratio,width,height))
            img = img.resize((width, height),Image.ANTIALIAS)
            if crop is not None:
                log.debug("in crop %s" % crop)
                crop = int(crop)
                if width > crop:
                    amt = int((int(width) - crop)/2)
                    img = img.crop((amt,0,amt + crop, crop))
                elif height > crop:
                    amt = int((int(height) - crop)/2)
                    img = img.crop((0,amt,crop,amt+crop))
            
            log.debug("saving new file %s" % new_file)
            img.save(new_file)
        
        
        if os.path.exists(local_path_wfile):
            if args != {}:
                ext = args['extension'] if 'extension' in args else "_t"
                resize_and_save(local_path_wfile,
                    '%s/%s%s.jpg' % (local_path,job['file'],ext),
                    maxsize=args['maxsize'],
                    crop=args['crop'])
            else:
                resize_and_save(local_path_wfile,'%s/%s_t.jpg' % (local_path,job['file']),maxsize=100)
                resize_and_save(local_path_wfile,'%s/%s_m.jpg' % (local_path,job['file']),maxw=317)
                resize_and_save(local_path_wfile,'%s/%s_l.jpg' % (local_path,job['file']),maxsize=800)
                keeptrying = False
        else:
            logging.error("haven't found file? %s" % local_path_wfile)
        
        # delete original
        logging.debug("About to delete original  %s" % local_path_wfile)
        os.remove(local_path_wfile)
    
    except:
        traceback.print_exc()

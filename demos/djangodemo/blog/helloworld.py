from django import http
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import loader, RequestContext
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from djangodemo.blog.models import Entry

from django.core.cache import cache
import datetime, re

def view(request,name='World'):
    if name == None or name == '':
        name = 'World'
    return HttpResponse("""<div>
        <h1>Secure Hello %s!</h1>
        This should be secure.  <br />
        Only visible to apps that have access as granted by demisauce or this app.  <br />
        Also, it should not be visible by phpdemo simply because php demo host's a service
        used by djangodemo. 
    </div>""" % (name))

def show(request,what='wat'):
    try:
        entry = Entry.objects.get(id=1)
    except ObjectDoesNotExist:
        print 'creating an item'
        entry = Entry(title="What's up?", pub_date=datetime.datetime.now(),content="this is a test article")
        entry.save()
    
    t = loader.get_template('hello_include.html')
    rc = RequestContext(request,{
        'entry': entry,
    })
    return HttpResponse(t.render(rc))
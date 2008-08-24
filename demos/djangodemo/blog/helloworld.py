from django import http
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.conf import settings
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

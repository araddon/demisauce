:tocdepth: 4

Demisauce Getting started with Django 
================================================

This tutorial will walk through the creation of a simple blog using `Demisauce <http://www.demisauce.com/>`_ 
services.  First, go to Demisauce and *signup* (top right) on demisauce.com, OR `install demisauce <http://github.com/araddon/demisauce/tree/1cd6ec9b9743bade739bb36bbde5630f877c1848/install>`_.  
Currently signups on demisauce.com are limited so send an email to the 
`discussion group <http://groups.google.com/group/demisauce>`_ and I will enable your account.  

The full source code for this application can be found on `Github <http://github.com/araddon/demisauce/tree/1cd6ec9b9743bade739bb36bbde5630f877c1848/demos/djangodemo>`_ so you can 
also pull from there and view that application.

=======================================
Create a Django Demo Application
=======================================

Create Django App
------------------
See the documentation on `Django Docs <http://docs.djangoproject.com/en/dev/intro/tutorial01/#intro-tutorial01>`_ 
and follow the part of installing and starting a new app, and where it says to create the app *polls* we will actually be 
createing an app called *blog*.
It is easiest to use Sqlite as the db for this demo::

    python manage.py startapp blog
    

Install Dependencies
---------------------
Install the Demisaucepy library by running::

    easy_install demisaucepy

First Demisauce Service
------------------------

Edit the *settings.py* and add the *djangodemo.blog* app and
also add the *demisaucepy.demidj* (demisauce django tags). ::
    
    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'demisaucepy.demidj',
        'djangodemo.blog'
    )
    

Now, edit the *settings.py* to add your demisauce configuration information.  First Go to your
demisauce account to get your *apikey*, click on the "Account" (after logging in), it should look like this

.. raw:: html
    
    <img src="http://demisaucepub.s3.amazonaws.com/s3/account.png" border="0" />
    

Then enter that apikey, and url to your *settings.py* like this::
    
    # apikey from account page, service url of demisauce server.
    DEMISAUCE_APIKEY = 'a95c21ee8e64cb5ff585b5f9b761b39d7cb9a202'
    DEMISAUCE_URL = 'http://localhost:4951'
    # your app name, used to make your urls unique
    DEMISAUCE_APPNAME = 'djangodemo'
    # if you have memcached
    CACHE_BACKEND = 'memcached://192.168.125.128:11211/'
    #CACHE_BACKEND = 'locmem:///'
    

Now Create a view following the `Django tuturial <http://docs.djangoproject.com/en/dev/intro/tutorial03/#intro-tutorial03>`_  
called *simple* by first adding to the urls.py::
    
    urlpatterns = patterns('',
        (r'^simple/$', 'djangodemo.blog.views.simple'),
    )

Then, add this to *simple.html*::
    
    {% load demisaucetags %}
    
    {% dsview "feedback" "badge" %}
    
And add this to your *blog/views.py*::
    
    from django.http import HttpResponse
    from django.template import loader, RequestContext
    from djangodemo.blog.models import Entry
    
    def simple(request):
        t = loader.get_template('simple.html')
        rc = RequestContext(request,{})
        return HttpResponse(t.render(rc))


and, your page should look like

.. raw:: html
    
    <img src="http://demisaucepub.s3.amazonaws.com/s3/firstbadge.png" border="0" />
    

So, now we have the basics of how to use a service from Demisauce.  The feedback badge is an
html service, to fully function it would need javascript as well.

Creating a Demisauce Mapped Service
------------------------------------

Demisauce python library currently provides a mapping layer, to allow local model objects to be related
to remote services, similar to ORM, where the service url's are automatically generated based on this relationship.  
We are going to add comments to our blog entry model, but first some style.  

Download a css/template from  `Free Css Templates <http://www.freecsstemplates.org/>`_ and
start working on the blog, add 3 new lines to the to the *url.py*:

.. code-block:: python
    
    urlpatterns = patterns('',
        (r'^simple/$', 'djangodemo.blog.views.simple'),
        (r'^$', 'djangodemo.blog.views.index'),
        (r'^blog/$', 'djangodemo.blog.views.index'),
        (r'^blog/view/(?P<id>\d+)', 'djangodemo.blog.views.view'),
    )

Create Models
--------------

Create the Entry class, edit the *blog/models.py* to resemble this:

.. code-block:: python

    from django.db import models
    from django.db.models.base import ModelBase
    from django.contrib import admin
    from demisaucepy.django_helper import ModelAggregatorMeta
    from demisaucepy.declarative import has_a, has_many, \
        AggregateView
    from django.contrib.auth.models import User

    class Entry(models.Model):
        __metaclass__ = ModelAggregatorMeta
        title = models.CharField(max_length=255)
        user = models.ForeignKey(User, unique=True)
        pub_date = models.DateTimeField('date published')
        content = models.TextField()
        comments = has_many(name='comment',lazy=True,local_key='id' )
        def __unicode__(self):
            return self.title

    admin.site.register(Entry)


Then run this from the command line to sync schema to DB::
    
    python manage.py syncdb


Creating Views
---------------

And add the new methods to *blog/views.py*, see the source at `github <http://github.com/araddon/demisauce/blob/1cd6ec9b9743bade739bb36bbde5630f877c1848/demos/djangodemo/blog/views.py>`_

.. code-block:: python
    
    def index(request):
        entry_list = Entry.objects.all().order_by('-pub_date')[:5]
        t = loader.get_template('index.html')
        rc = RequestContext(request,{
            'entry_list': entry_list,
        })
        return HttpResponse(t.render(rc))
    
    def view(request,id=''):
        entry_list = [Entry.objects.get(id=id)]
    
        #for passing cookie header info
        # note this is only if you trust the destination
        Entry.comments.add_request(request.REQUEST)
        t = loader.get_template('index.html')
        rc = RequestContext(request,{
            'entry_list': entry_list,
            'show_comments':True
        })
        return HttpResponse(t.render(rc))

Now create the *index.html* view page. 

.. code-block:: python
    
    {% extends "base.html" %}
    {% load demisaucetags %}
    {% block content %}
    {% if entry_list %}
        {% for entry in entry_list %}
        <div class="post">
            <h1 class="title"><a href="/blog/view/{{ entry.id }}">{{ entry.title }}</a></h1>
            <p class="byline"><small>Posted on {{ entry.pub_date|date:"F d, Y" }} 
            
                by <a href="#">admin</a> | <a href="#">Edit</a></small></p>
            <div class="entry">
                {{ entry.content }}
            </div>
            <p class="meta">
                <a href="#" class="more">Read More</a> &nbsp;&nbsp;&nbsp; 
                <a href="#" class="comments">Comments (33)</a></p>
            {% if show_comments %}
                {% if entry.comments %}
                    {% autoescape off %}
                    
                    {{ entry.comments.views.summary }}
                    {% endautoescape %}
                
                {% else %}
                no comments
                {% endif %}
            {% endif %}
        </div>
        {% endfor %}
    
    {% else %}
        <p>No entries are available.</p>
    {% endif %}
    
    {% endblock %}


The end result should be a page with comments related to entries  (Entries were created in 
`Django admin <http://docs.djangoproject.com/en/dev/intro/tutorial02/#intro-tutorial02>`_ )


Output

.. raw:: html
    
    <img src="http://demisaucepub.s3.amazonaws.com/s3/demoblog.png" border="0" />
    

from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    # Example:
    # (r'^djangodemo/', include('djangodemo.foo.urls')),

    # Uncomment the next line to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    
    # Uncomment the next line for to enable the admin:
    #(r'^blog/(.*)', djangodemo.blog.views),
    (r'^blog/$', 'djangodemo.blog.views.index'),
    (r'^blog/view/(?P<id>\d+)', 'djangodemo.blog.views.view'),
    (r'^status/cache/$', 'djangodemo.blog.memcached_status.view'),
    (r'^service/helloworld/(.*)', 'djangodemo.blog.helloworld.view'),
    
    

    # Uncomment the next line for to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)

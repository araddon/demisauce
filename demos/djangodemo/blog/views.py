import logging
from django.http import HttpResponse
from django.template import loader, RequestContext
from djangodemo.blog.models import Entry
from django.core.cache import cache

log = logging.getLogger(__name__)

def simple(request):
    t = loader.get_template('simple.html')
    rc = RequestContext(request,{})
    return HttpResponse(t.render(rc))

def index(request):
    entry_list = Entry.objects.all().order_by('-pub_date')[:5]
    log.debug('entry_list ct = %s' % len(entry_list))
    t = loader.get_template('index.html')
    rc = RequestContext(request,{
        'entry_list': entry_list,
    })
    #cache.delete('e3bc6199e87646230dd144246318eea2') # service definition
    return HttpResponse(t.render(rc))

def view(request,id=''):
    entry_list = [Entry.objects.get(id=id)]
    
    #for passing cookie header info
    Entry.comments.add_request(request.REQUEST)
    #for entry in entry_list:
    #    log.debug(dir(entry))
    temp ="""
    for entry in entry_list:
        if entry.comments.model:
            for comment in entry.comments.model:
                print comment.created
    """
    t = loader.get_template('index.html')
    rc = RequestContext(request,{
        'entry_list': entry_list,
        'show_comments':True
    })
    return HttpResponse(t.render(rc))

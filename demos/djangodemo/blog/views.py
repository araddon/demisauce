import logging
from django.http import HttpResponse
from django.template import loader, RequestContext
from djangodemo.blog.models import Entry
from django.core.cache import cache

log = logging.getLogger(__name__)

def index(request):
    entry_list = Entry.objects.all().order_by('-pub_date')[:5]
    log.debug('entry_list ct = %s' % len(entry_list))
    t = loader.get_template('index.html')
    rc = RequestContext(request,{
        'entry_list': entry_list,
    })
    #cache.delete('e3bc6199e87646230dd144246318eea2') # service definition
    #cache.delete('d3a6ac5d5c0f2ce6a9d647a08b36debd') # feedback badge html
    #cache.delete('a9e72e94a16e5e65f9acc9b9a83ca049') # poll service
    #cache.delete('0ebe41b686e32db935e18b92e7ea9ee3')  #phphelloworld service
    #log.debug(dir(request.user))
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

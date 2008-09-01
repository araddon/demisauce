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
    
    return HttpResponse(t.render(rc))

def view(request,id=''):
    entry_list = [Entry.objects.get(id=id)]
    #cache.add('hello_aaron',10)
    #temp = cache.get('hello_aaron')
    #print 'cache val = %s' % (temp)
    
    
    #Yuck!  TODO: fix this to something more elegant. 
    Entry.comments.add_request(request.REQUEST)
    for entry in entry_list:
        entry.comments.add_cookies(request.COOKIES)
        #print entry.comments.views.summary
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

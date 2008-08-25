from django.http import HttpResponse
from django.template import loader, RequestContext

from djangodemo.blog.models import Entry

from django.core.cache import cache



def index(request):
    entry_list = Entry.objects.all().order_by('-pub_date')[:5]
    t = loader.get_template('index.html')
    rc = RequestContext(request,{
        'entry_list': entry_list,
    })
    return HttpResponse(t.render(rc))

def view(request,id=''):
    entry_list = [Entry.objects.get(id=id)]
    cache.add('hello_aaron',10)
    temp = cache.get('hello_aaron')
    print 'cache val = %s' % (temp)
    #Yuck!  TODO: fix this to something more elegant. 
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

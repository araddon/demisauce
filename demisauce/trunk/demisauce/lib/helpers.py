"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
import os, logging
import webhelpers
from webhelpers.html import tags
from webhelpers import text
from tornado.options import options
import urllib, hashlib
from webhelpers.html.tags import select
import webhelpers.paginate
import math

teststring = 'good'
def wordpress_page():
    """Get a wordpress page"""
    pass

def dspager(qry,perpage=15):
    temp = """
    <div class="boxlinks boxlinks_tabs">
    <span class="nextprev">&#171; Previous</span>
    <span class="current">1</span>
    <a title="Go to page 2" href="/news/page2">2</a>
    <a title="Go to page 3" href="/news/page3">3</a>
    <a title="Go to page 4" href="/news/page4">4</a>
    <a title="Go to page 5" href="/news/page5">5</a>
    <a title="Go to page 6" href="/news/page6">6</a>
    <a title="Go to page 7" href="/news/page7">7</a>
    <a title="Go to page 8" href="/news/page8">8</a>
    <a title="Go to page 9" href="/news/page9">9</a>
    <a title="Go to page 10" href="/news/page10">10</a>
    <span></span>
    <a title="Go to page 163" href="/news/page163">163</a>
    <a title="Go to page 164" href="/news/page164">164</a>
    <a class="nextprev" title="Go to Next Page" href="/news/page2">Next &#187;</a>
    </div>
    ${c.groups.pager('Page $page: $link_previous ~4~ ',symbol_next='',symbol_previous='< Prev ')}
    """
    page = 1
    if 'page' in request.params:
        page = int(request.params['page'])
    qry = webhelpers.paginate.Page(qry,page=page,items_per_page=perpage)
    qry.dspagerhtml = dspager2(qry)
    return qry

def dspager2(pgr):
    p = pgr.pager('''<div class="boxlinks boxlinks_tabs">$link_previous ~4~ $link_next </div>''',
        symbol_next=' Next >> ',symbol_previous='<< Prev ', curpage_attr={'class': 'current'})
    return p.replace('&gt;&gt;','&#187;').replace('&lt;&lt;','&#171;')

def route_url(includeaction=True):
    """ Returns the url minus id, so controller/action typically"""
    url = ''
    if 'controller' in request.environ['pylons.routes_dict']:
        url += '/%s' % request.environ['pylons.routes_dict']['controller']
    if includeaction and 'action' in request.environ['pylons.routes_dict']:
        url += '/%s' % request.environ['pylons.routes_dict']['action']
    return url
    

def help_url(includeaction=True):
    """Returns the Html for the page you are on"""
    url = '/api/script/cms/root/help%s' % route_url(includeaction)
    return url

def current_url(includeaction=True):
    """ Returns the url minus id, so controller/action typically"""
    url = ''
    if 'controller' in request.environ['pylons.routes_dict']:
        url += '/%s' % request.environ['pylons.routes_dict']['controller']
    if includeaction and 'action' in request.environ['pylons.routes_dict']:
        url += '/%s' % request.environ['pylons.routes_dict']['action']
    return url

def is_current_filter(filter='',value=''):
    filters = request.environ['filters']
    toreturn = 'current'
    if filter == None or filters == None or filters.context == '':
        return ''
    fltr = filters.current()
    if not hasattr(fltr, "clauses"):
        return ''
    for k in fltr.clauses.keys():
        if fltr.clauses[k] == value:
            return toreturn
    return ''

def is_current(url,matchlist,toreturn="current",requestargs={}):
    """
    Determines if current http request uri matches the passed in nav item
    """
    for match in matchlist:
        if match == None:
            if url == '/':
                return toreturn
        elif url.find(match) >= 0:
            return toreturn
        elif match.find('=') > 0:
            ml = match.split('=')
            if ml[0] in requestargs and requestargs[ml[0]] == ml[1]:
                return toreturn
    return ""

def is_currentqs(matchlist,toreturn="current"):
    """
    Determines if current http request uri querhstring
    matches the passed in nav item
    """
    for match in matchlist:
        if match in request.params:
            return toreturn
    return ""

htmlCodes = [
    ['&', '&amp;'],
    ['<', '&lt;'],
    ['>', '&gt;'],
    ['"', '&quot;'],
]
htmlCodesReversed = htmlCodes[:]
htmlCodesReversed.reverse()


def remote_html(resource_id='',routes_dict=None,append_path=False,**kwargs):
    from demisaucepy.pylons_helper import remote_html
    return remote_html(resource_id=resource_id,
        routes_dict=routes_dict,append_path=append_path,**kwargs)

def html_encode(s, codes=htmlCodes):
    """ Returns the HTML encoded version of the given string. This is useful to
    display a plain ASCII text string on a web page."""
    for code in codes:
        s = s.replace(code[0], code[1])
    return s

def isdemisauce_admin():
    """
    Determines if current user is DemiSauce admin, and if so will show
    a link to Demisauce admin to add items that don't exist
    """
    if not self.user:
        return False
    elif self.user.id == 1:
        return True
    return False

def tag_links(site_id=0,tag_type=None,tags=None,cachetime=180):
    """
    Converts a list of tags to a list of links
    :tag_type: the type since tags can refer to many things
    
    """
    selected_tags = tags
    def tag_make():
        from demisauce.model.tag import Tag
        alltags = Tag.by_key(site_id=site_id,tag_type=tag_type)
        tag_links = []
        for tag in alltags:
            if tag in selected_tags:
                tag_links.append('''<a href="#" id="tag_%s" class="tagged">%s</a>''' % (tag.replace(':',''),tag))
            else:
                tag_links.append("<a href=\"#\" id=\"tag_%s\">%s</a>" % (tag.replace(':',''),tag))
        return '  '.join(tag_links)
    
    mycache = cache.get_cache('demisauce.tags' )
    # Get the value, this will create the cache copy the first time
    # and any time it expires (in seconds, so 3600 = one hour)
    myvalue = mycache.get_value('tag.%s.linklist' % (tag_type), 
        createfunc=tag_make,expiretime=cachetime)
    return myvalue

def tag_weight(x):
    if x==None or x==0:
         x = 1
    return 70 + 32 * math.log(x, math.e)

def tag_cloud(site_id=0,tag_type=None,link='',cachetime=180):
    """tag cloud"""
    def tag_make():
        from demisauce.model.tag import Tag
        alltags = Tag.by_cloud(site_id=site_id,tag_type=tag_type)
        tag_links = []
        tagct = [t[1] for t in alltags]
        #  max size = 150%, min size = 50%
        # if 100 tags, max = 20, min =1
        for row in alltags:
            tag_links.append('''<a href="%s%s" id="tag_%s" class="tagged" 
                style="font-size:%s%s">%s</a>''' % (link,row[0],row[0],tag_weight(row[1]),'%',row[0]))
        return '  '.join(tag_links)
    
    mycache = cache.get_cache('demisauce.tagss' )
    # Get the value, this will create the cache copy the first time
    # and any time it expires (in seconds, so 3600 = one hour)
    myvalue = mycache.get_value('tag.%s.linkcloud' % (tag_type), 
        createfunc=tag_make,expiretime=cachetime)
    return myvalue

def round_box(html_content):
    return """<div class="corner_box statusmsgboxrc tempmessage">
                <div class="corner_top"><div></div></div>
                   <div class="corner_content">
                      %s
                   </div>
                <div class="corner_bottom"><div></div></div>
             </div>""" % (html_content)



truncate = text.truncate

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']


_filters = {"dspager":dspager,
            "is_current":is_current,
            "tag_cloud":tag_cloud,
            "tag_links":tag_links}
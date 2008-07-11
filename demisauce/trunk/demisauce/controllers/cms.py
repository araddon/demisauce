#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
from sqlalchemy.orm import eagerload
from sqlalchemy.sql import and_

from demisauce.model import mapping
from demisauce.lib.base import *
from demisauce.lib.helpers import *
from demisauce import model
from demisauce.model.cms import Cmsitem


log = logging.getLogger(__name__)


class CmsForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    title = formencode.All(String(not_empty=True))

def find_folder_or_create(key,parentid):
    """
    for requested folder path/key/context, see if they already exist.
    else if we know parentid, then use that instead since we know we aren't
    creating
    """
    keys = key.split('/')
    # if they knew the parent id, handle here
    if parentid and int(parentid):
        parent = meta.DBSession.query(Cmsitem).filter_by(site_id=c.site_id,
                                    id=parentid).first()
        if parent and parent.id > 0:
            return parent,key
    
    # didn't know, maybe using text based folders not id's
    root = meta.DBSession.query(Cmsitem).filter_by(site_id=c.site_id,
                                    item_type='root').first()
    nextparent = root
    # find folder/context path from text matches
    if keys and len(keys) > 1:
        # in a folder
        for k in keys[:len(keys)-1]:
            if k == '':
                pass  #  /afolder/waslikethis  with leading /
            elif k == 'root':
                pass
            else:
                f = meta.DBSession.query(Cmsitem).filter(and_(Cmsitem.item_type=='folder',
                    Cmsitem.site_id==c.site_id, Cmsitem.key==k)).first()
                if f == None and k != 'root':
                    newf = Cmsitem(c.site_id, k,k)
                    newf.key = k
                    newf.rid = '%s%s' % (nextparent.rid and (nextparent.rid + '/') or '',k)
                    newf.item_type = 'folder'
                    nextparent.addChild(newf)
                    nextparent = newf
                elif f == None:
                    pass
                else:
                    root = f
                    nextparent = f
    
    root.save()
    return nextparent,keys[len(keys)-1]


def updaterid(parent):
    for associtem in parent.children:
        #print '%s%s' % (parent.rid and (parent.rid + '/') or '',associtem.item.key)
        associtem.item.rid = '%s%s' % (parent.rid and (parent.rid + '/') or '',associtem.item.key)
        print associtem.item.rid
        updaterid(associtem.item)


class CmsController(SecureController):
    """
    The Main content type controller
    """
    requires_auth = True
    
    @rest.dispatch_on(POST="addupdate")
    def index(self,id=0):
        c.isroot = False
        if id > 0:
            c.item = [meta.DBSession.query(Cmsitem).get(id)]
        else:
            c.isroot = True
        
        c.root = meta.DBSession.query(Cmsitem).options(eagerload('children')
                    ).filter_by(site_id=c.site_id,item_type='root').first()
        
        return render('/cms.html')
    
    @rest.dispatch_on(POST="addupdate")
    def add(self,key=''):
        model.make_key(key.lower())
        c.item = Cmsitem(c.site_id, key,'')
        keys = key.split('/')
        c.item.key = keys[len(keys)-1]
        c.item.rid = '/'.join([s for s in keys if s != c.item.key])
        c.root = meta.DBSession.query(Cmsitem).options(eagerload('children')
                    ).filter_by(site_id=c.site_id,item_type='root').first()
        return render('/cms.html')
    
    @rest.dispatch_on(POST="addupdate")
    def additem(self,key=''):
        key = urllib.unquote_plus(key)
        key = key.replace(' ','')
        c.item = Cmsitem(c.site_id, key,'')
        c.item.key = key
        return render('/cms_edit.html')
    
    @rest.dispatch_on(POST="addupdate")
    def addfolder(self,id=0):
        #print 'addfolder id=%s' % id
        c.item = Cmsitem(c.site_id, '','')
        c.item.key = ''
        c.item.item_type = 'folder'
        return render('/cms_edit.html')
    
    def keygen(self):
        title = request.POST['title']
        key = model.make_key(title.lower())
        return key
    
    #@rest.dispatch_on(POST="addupdate")
    def view(self,key=''):
        if not key == '':
            key = urllib.unquote_plus(key)
            c.cmsitems = meta.DBSession.query(Cmsitem).filter_by(key=key).all()
        else:
            c.cmsitems = meta.DBSession.query(Cmsitem).all()
        return render('/cms.html')
    
    @validate(schema=CmsForm(), form='index')
    def addupdate(self):
        key = self.form_result['key']
        if self.form_result['objectid'] == "0":
            rid = self.form_result['rid']
            key2 = '%s%s' % (rid and (rid + '/') or '',key)
            parent,key2 = find_folder_or_create(key2,self.form_result['parentid'])
            item = Cmsitem(c.site_id, self.form_result['title'],
                           self.form_result['content'])
            item.item_type = self.form_result['item_type']
            parent.addChild(item)
            parent.save()
        else:
            id = self.form_result['objectid']
            item = meta.DBSession.query(Cmsitem).filter_by(id=id,site_id=c.site_id).first()
            item.title = self.form_result['title']
            item.content = self.form_result['content']
        
        parent = item.parents[0].parent
        item.rid = '%s%s' % (parent.rid and (parent.rid + '/') or '',key)
        item.key = key
        item.tags = self.form_result['tags']
        item.url = self.form_result['url']
        item.content2 = self.form_result['content2']

        item.save()
        h.add_alert('updated item')
        c.cmsitems = [item]
        if 'returnurl' in request.params:
            redirect_to(request.params['returnurl'])
        return self.view()
        return item.id
    
    def reorder(self,id=0):
        c.item = meta.DBSession.query(Cmsitem).filter_by(
            id=id,site_id=c.site_id).first()

        ids = [int(i) for i in request.POST['ids'].split(',') if i != '']
        if c.item and c.item.children and len(c.item.children) > 0:
            for cassoc in c.item.children:
                #print 'cassoc.item.id=%s   position=%s' % (cassoc.item.id,cassoc.position)
                pos = 0
                for i in ids:
                    pos += 1
                    if i == cassoc.item.id:
                        cassoc.position = pos
                    
                #print 'cassoc.item.id=%s   position=%s' % (cassoc.item.id,cassoc.position)
            c.item.save()
        else:
              return 'no parent?'
        
        return "Updated"
    
    def edit(self,id=0):
        c.item = meta.DBSession.query(Cmsitem).filter_by(
            id=id,site_id=c.site_id).first()
        
        return render('/cms_edit.html')
    
    def delete(self,id=0):
        cmsitem = meta.DBSession.query(Cmsitem).filter_by(
            id=id,site_id=c.site_id).first()
        cmsitem.delete()
        return ''
    
    def updaterid(self,id=0):
        root = meta.DBSession.query(Cmsitem).options(eagerload('children')
                ).filter_by(item_type='root',site_id=c.site_id).first()
        
        s = ''
        print 'root rid=%s' % root.rid
        updaterid(root)
        root.save()
        return ''
    
    def viewfolder(self,id=0):
        c.item = meta.DBSession.query(Cmsitem).filter_by(
            id=id,site_id=c.site_id).first()
        
        return render('/cms_view.html')
    


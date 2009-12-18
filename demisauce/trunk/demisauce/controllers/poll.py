#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode
import tempita
#from sqlalchemy.orm import eagerload

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import meta, mapping
from demisauce.model.poll import *

log = logging.getLogger(__name__)

def poll_html(poll):
    htmlid = 'ds-poll-results-%s' % poll.id
    poll.results = rendertf('/poll/poll_results.html',locals())
    results = poll.results
    poll.html = rendertf('/poll/poll_public.html',locals())

class PollFormValidation(formencode.Schema):
    """Form validation for the poll web admin"""
    allow_extra_fields = True
    filter_extra_fields = False
    name = formencode.All(String(not_empty=True))
    question = formencode.All(String(not_empty=True))

class PollpublicController(BaseController):
    def vote(self,id=''):
        if id != '' and id != None:
            id = urllib.unquote_plus(id)
        verb = request.environ['REQUEST_METHOD'].lower()
        if verb == 'get':
            if 'poll_id' in request.params:
                p = poll.Poll.getsa(int(request.params['poll_id']))
        
        elif verb == 'post' or verb == 'put':
            if 'poll_id' in request.params:
                p = poll.Poll.getsa(int(request.params['poll_id']))
                #p.description = request.params['description']
            #p.save()
            c.polls = [p]
        self.render('/poll/poll_results.html')
    

class PollController(SecureController):
    
    @rest.dispatch_on(POST="addupdate")
    def index(self,id=0):
        if id > 0:
            c.items = [meta.DBSession.query(Poll).get(id)]
        else:
            c.items = meta.DBSession.query(Poll).filter_by(site_id=self.user.site_id).all()
        self.render('/poll/poll.html')
    
    @validate(schema=PollFormValidation(), form='edit')
    def addupdate(self,id=0):
        if self.form_result['poll_id'] == "0":
            item = Poll(site_id=c.site_id, name=self.form_result['name'])
            item.author = model.person.Person.get(c.site_id,self.user.id)
        else:
            id = self.form_result['poll_id']
            item = Poll.get(c.site_id,id)
            item.name = self.form_result['name']
        
        item.key = sanitize(self.form_result['real_permalink'])
        item.description = sanitize(self.form_result['description'])
        if 'allow_anonymous' in self.form_result:
            item.allow_anonymous = self.form_result['allow_anonymous']
        if 'css' in self.form_result:
            item.css = self.form_result['css']
        item.save()
        q2 = sanitize(self.form_result['question'])
        #print 'q_ids %s' % self.form_result['q_ids']
        for qid in [t for t in self.form_result['q_ids'].strip().split(',') if t != '']:
            q = item.get_question(int(qid))
            if 'question_type' in self.form_result:
                q.type = self.form_result['question_type']
            #for o in self.form_result['question_option']:
            #    q.add_or_update_option(o)
        poll_html(item)
        item.save()
        h.add_alert('updated poll')
        return redirect_wsave('/poll')
    
    def _process_poll(self):
        item = None
        if 'poll_id' in self.request.arguments:
            if self.request.arguments['poll_id'] == "0":
                item = Poll(site_id=c.site_id, name=sanitize(self.request.arguments['name']))
                item.person_id = self.user.id
                item.key = self.request.arguments['key']
                if self.user:
                    item.person_id = self.user.id
            else:
                id = self.request.arguments['poll_id']
                item = Poll.get(c.site_id,int(id))
                item.name = sanitize(self.request.arguments['name'])
        return item
    
    def optionupdate(self):
        if ('q_id' in self.request.arguments and 'poll_id' in self.request.arguments and 'o_id' 
            in self.request.arguments):
            poll = Poll.get(self.user.site_id,int(self.request.arguments['poll_id']))
            q = poll.questions[0]
            #q = poll.get_question(int(self.request.arguments['q_id']))
            o = q.add_or_update_option(sanitize(self.request.arguments['question_option']),
                    int(self.request.arguments['o_id']))
            poll.save()
        return '{poll:{id:%s,o_id:%s}}' % (poll.id,q.id)
    
    def postquestion(self,id=0):
        item = self._process_poll()
        if item:
            item.save()
            if self.request.arguments['q_id'] == "0":
                q = Question(question=sanitize(self.request.arguments['question']))
                item.questions.append(q)
            else:
                id = self.request.arguments['q_id']
                q = item.get_question(int(id))
                q.question = sanitize(self.request.arguments['question'])
            poll_html(item)
            item.save()
        return '{poll:{id:%s,q_id:%s}}' % (item.id,q.id)
    
    @rest.dispatch_on(POST="addupdate")
    def edit(self,id=0):
        c.item = Poll.get(self.user.site_id,id)
        self.render('/poll/poll_edit.html')
    
    def sort(self):
        if 'q_id' in self.request.arguments and 'poll_id' in self.request.arguments:
            poll = Poll.get(self.user.site_id,int(self.request.arguments['poll_id']))
            q = poll.questions[0]
            if 'question_option' in request.params:
                for o in request.params.getall('question_option'):
                    #print 'oo = %s' % o
                    q.add_or_update_option(o)
            if 'o_id' in request.params:
                sort_order = 0
                for oid in request.params.getall('o_id'):
                    #print 'oid = %s, sort_order=%s' % (oid,sort_order)
                    q.change_sort_order(oid,sort_order)
                    sort_order += 1
            poll_html(poll)
            poll.save()
        return '{poll:{id:%s,q_id:%s}}' % (1,2)
    
    def view(self,id=0):
        """view a poll"""
        c.item = Poll.by_key(self.user.site_id,id)
        c.item_html = c.item.html
        self.render('/poll/poll_view.html')
    
    def polldelete(self,id=0):
        if id > 0:
            p = Poll.get(self.user.site_id,id)
            p.delete()

        return '{msg:"updated"}'
    
    def delete(self,id=0):
        if 'oid' in self.request.arguments:
            oid = int(self.request.arguments['oid'])
            o = QuestionOption.saget(oid)
            if o and self.user.site_id == o.question.poll.site_id:
                o.delete()
        
        return '{msg:"updated"}'
    


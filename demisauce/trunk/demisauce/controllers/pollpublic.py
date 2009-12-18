#!/usr/bin/env python
import logging
import urllib
import simplejson
from pylons import config

from demisauce.lib.base import *
from demisauce.controllers.poll import poll_html
from demisauce.model.poll import Poll, Question, PollResponse, \
    PollAnswer

log = logging.getLogger(__name__)

class PollpublicController(BaseController):
    def index(self):
        poll = {'poll_id':1,'name':"good"}
        qid = 2
        self.rendertf('/poll/poll_results.html',locals())
    
    def display(self,id=''):
        p = Poll.by_key(0,id)
        if p == None or p.results == None:
            poll_html(p)
            p.save()
        data = {'success':True,'html':'%s %s' % (p.html,p.results)}
        json = simplejson.dumps(data)
        response.headers['Content-Type'] = 'text/json'
        return '%s(%s)' % (request.params['jsoncallback'],json)
    
    def show_results(self,id=''):
        p = Poll.by_key(0,id)
        data = {'success':True,'html':p.results}
        json = simplejson.dumps(data)
        response.headers['Content-Type'] = 'text/json'
        return '%s(%s)' % (request.params['jsoncallback'],json)
    
    def vote(self,id=''):
        p = None
        if id != '' and id != None:
            id = urllib.unquote_plus(id)
        verb = request.environ['REQUEST_METHOD'].lower()
        if verb == 'get' and 'jsoncallback' in request.params:
            if ('poll_id' in request.params and 'q_id' in request.params \
                and 'options' in request.params):
                options = request.params['options']
                poll = Poll.saget(int(request.params['poll_id']))
                q = poll.get_question(int(request.params['q_id']))
                if self.user:
                    pollresponse = PollResponse(person_id=self.user.id)
                else:
                    pollresponse = PollResponse(person_id=0)
                oid = int(request.params['options'])
                a = PollAnswer(question_id=q.id,option_id=oid) #TODO make work for many answers
                pollresponse.answers.append(a)
                poll.responses.append(pollresponse)
                poll.save()
                poll.update_vote(pollresponse)
                htmlid = 'ds-poll-results-%s' % poll.id
                poll_html(poll)
                poll.save()
        
        data = {'success':True,'html':poll.results,'key':poll.key,'htmlid':htmlid}
        json = simplejson.dumps(data)
        response.headers['Content-Type'] = 'text/json'
        return '%s(%s)' % (request.params['jsoncallback'],json)
    


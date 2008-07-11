#!/usr/bin/env python
import logging
import urllib
import simplejson
from pylons import config

from demisauce.lib.base import *
from demisauce.model.poll import Poll, Question, PollResponse, \
    PollAnswer

log = logging.getLogger(__name__)

class PollpublicController(BaseController):
    def index(self):
        poll = {'poll_id':1,'name':"good"}
        qid = 2
        return rendertf('/poll/poll_results.html',locals())
    
    def vote(self,id=''):
        p = None
        for par in request.params:
            print 'par=%s, val=%s' % (par,request.params[par])
        if id != '' and id != None:
            id = urllib.unquote_plus(id)
        verb = request.environ['REQUEST_METHOD'].lower()
        if verb == 'get' and 'jsoncallback' in request.params:
            print 'in json post'
            if ('poll_id' in request.params and 'q_id' in request.params \
                and 'options' in request.params):
                options = request.params['options']
                print 'options = %s' % (options)
                p = Poll.saget(int(request.params['poll_id']))
                q = p.get_question(int(request.params['q_id']))
                if c.user:
                    response = PollResponse(c.user.id)
                else:
                    response = PollResponse(0)
                for oid in request.params['options']:
                    print oid
                oid = int(request.params['options'])
                a = PollAnswer(q.id,oid) #TODO make work for many answers
                response.answers.append(a)
                p.responses.append(response)
                p.save()
                p.update_vote(response)
                print 'answerid = %s' % (response.id)
        elif verb == 'get' 'poll_id' in request.params:
            print 'in regular get??? poll_id?'
        temp = """
        if verb == 'get':
            log.debug('in get')
            if 'poll_id' in request.params:
                p = Poll.saget(int(request.params['poll_id']))
        elif verb == 'post' or verb == 'put':
            if True == True:
                '''  (('poll_id' in request.params))
                and ('q_id' in request.params)
                    and ('options' in request.params)
                par=poll_id, val=2
                par=q_id, val=2
                par=options, val=19
                '''
                p = Poll.getsa(int(request.params['poll_id']))
                q = p.get_question(int(request.params['q_id']))
                if c.user:
                    response = PollResponse(c.user.id)
                else:
                    response = PollResponse(0)
                for oid in request.params['options']:
                    print oid
                    response.answers.append(poll.PollAnswer(q.id,oid))
                p.responses.append(response)
                p.save()
                #p.description = request.params['description']
            #p.save()
            c.polls = [p]
        """
        poll = p
        html = rendertf('/poll/poll_results.html',locals())
        data = {'success':True,'html':html}
        json = simplejson.dumps(data)
        #print json
        return '%s(%s)' % (request.params['jsoncallback'],json)

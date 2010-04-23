"""
This is the base content item
"""
import logging
import json
from tornado.options import options
from demisaucepy.tests import *
from demisaucepy import demisauce_ws_get, httpfetch
from demisaucepy import mail
from demisaucepy.cache import cache


log = logging.getLogger("dspy.tests")

def test_email():
    "test if we can send an email"
    #options.'smtp_server'] == 'mockserver.com' # force mock smtp connect
    data = {'subject':'test email',
        'message':'test body', 
        "from_email":'Test Sender<test@fake.com>', 
        "recipient_list":'tester@email.com')
    num_sent = mail.send_mail_toeach(data)
    assert num_sent == 1
    
    data['recipient_list'] = ['tester@email.com','teste2r@email.com']
    num_sent = mail.send_mail_toeach(data)
    assert num_sent == 2
    
    mockserver = mail.get_smtp_server('mockserver.com')
    assert type(mockserver) == mail.mocksmtp
    assert mockserver.server_address == 'mockserver.com'
    num_sent = mail.send_email(data), 
            to_each=True,server=mockserver)
    assert num_sent == 2
    assert len(mockserver.messages) == 2
    assert mockserver.closed == False
    mockserver.end()
    assert mockserver.closed == True

def test_emailsend():
    "test if we can send an email"
    from gearman import GearmanClient
    from gearman.task import Task
    gearman_client = GearmanClient(options.gearman_servers)
    #send emails
    jsondict = {
        'template_name':'thank_you_for_registering_with_demisauce',
        'emails':['araddon@yahoo.com'],
        'template_data':{
            'displayname':'Bob User',
            'title':'welcome',
            'email':'araddon@yahoo.com',
            'link':'http://www.demisauce.com/?fake=testing'
        }
    }
    num_sent = gearman_client.do_task(Task("email_send",json.dumps(jsondict), background=False))
    logging.debug("test emailsend num_sent = %s" % (num_sent))
    assert num_sent == '1'

def test_email_native():
    "test if we can send an email by embedding entire message template"
    from gearman import GearmanClient
    from gearman.task import Task
    gearman_client = GearmanClient(options.gearman_servers)
    #send emails by passing the template
    jsondict = {
        'template':'This tests templating',
        'emails':['araddon@yahoo.com'],
        'template_data':{
            'displayname':'Bob User',
            'title':'welcome',
            'link':'http://www.demisauce.com/?fake=testing'
        }
    }
    #num_sent = gearman_client.do_task(Task("email_send",json.dumps(jsondict), background=False))
    #assert num_sent == '1'
    #assert True == False
    #send emails by passing the message body
    jsondict = {
        'message':'This tests messaging, no template',
        'emails':['araddon@yahoo.com'],
    }
    #num_sent = gearman_client.do_task(Task("email_send",json.dumps(jsondict), background=False))
    #assert num_sent == '1'

def test_email_via_webhook():
    "Post an http web hook call to ds with request to send email"
    jsondict = {
        'template_name':'thank_you_for_registering_with_demisauce',
        'emails':['araddon@yahoo.com'],
        'template_data':{
            'displayname':'Bob User',
            'title':'welcome',
            'email':'araddon@yahoo.com',
            'link':'http://www.demisauce.com/?fake=testing'
        }
    }
    data = json.dumps(jsondict)
    url = "http://localhost:4950/api/email/thank_you_for_registering_with_demisauce/send.json?apikey=a95c21ee8e64cb5ff585b5f9b761b39d7cb9a202"
    response = httpfetch.fetch(url, data=data)
    assert response['status'] == 200
    assert 'data' in response


import json
import logging
import urllib, time, string
import sys, traceback
from string import Template
import base64
from demisaucepy import mail
from demisaucepy import demisauce_ws


def email_send(job_object):
    """Email background sendor
    format::
        
        jsondict = {
            'apikey':'optional val to override ds default',
            'template_name':'thank_you_for_registering_with_demisauce',
            'emails':['afakeuser@email.com'],
            'template_data':{
                'displayname':'Bob User',
                'title':'welcome',
                'email':'afakeuser@email.com',
                'link':'http://www.demisauce.com/?go'
            }
        }
        gearman_client.do_task(Task("email_send",json.dumps(jsondict), background=True))
    """
    try:
        emailargs = json.loads(job_object.arg)
        email_name = urllib.quote_plus(emailargs['template_name'])
        if 'apikey' in emailargs:
            response = demisauce_ws('email',email_name,cache=True,apikey=emailargs['apikey'])
        else:
            response = demisauce_ws('email',email_name,cache=True)
        if response.success and response.json and len(response.json) ==1:
            emailjson = response.json[0]
            s = Template(emailjson['template'])
            sh = Template(emailjson['template'])
            if emailjson['template_html'] not in (None,''):
                sh = Template(emailjson['template_html'])
            if 'template_data' in emailargs:
                template = s.substitute(emailargs['template_data'])
                templateh = sh.substitute(emailargs['template_data'])
            else:
                template = s.substitute({})
                templateh = sh.substitute({})
            #tuple:  (subject, body, to<to@email.com>, [recipient1@email.com,recipient2@email.com])
            data = {'subject': emailjson['subject'],
                'message':template, 
                'from_email':'%s<%s>' % (emailjson['from_name'],emailjson['from_email']), 
                'recipient_list': emailargs['emails'],
                'message_html': templateh}
            num_sent = mail.send_mail_toeach(data)
            logging.info('sent email to %s, num_sent = %s' % (emailargs['emails'], num_sent))
            return num_sent
        else:
            #logging.error("len json = %s" % (len(response.json)))
            logging.error('Error retrieving that template %s  \n\n %s' % (emailargs,response.json))
            return -1
    except:
        #logging.error("Error in gearman task email_send:  %s" % err)
        traceback.print_exc()
        return -1


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


log = logging.getLogger(__name__)

class TestEmail(TestDSBase):
    def test_email(self):
        "test if we can send an email"
        #options.'smtp_server'] == 'mockserver.com' # force mock smtp connect
        num_sent = mail.send_mail_toeach(('test email',
            'test body', 
            'Test Sender<test@fake.com>', 
            'tester@email.com'))
        assert num_sent == 1
        
        num_sent = mail.send_mail_toeach(('test email',
            'test body', 
            'Test Sender<test@fake.com>', 
            ['tester@email.com','teste2r@email.com']))
        assert num_sent == 2
        
        mockserver = mail.get_smtp_server('mockserver.com')
        assert type(mockserver) == mail.mocksmtp
        assert mockserver.server_address == 'mockserver.com'
        num_sent = mail.send_email(('test email',
            'test body', 
            'Test Sender<test@fake.com>', 
            ['tester@email.com','teste2r@email.com']), 
                to_each=True,server=mockserver)
        assert num_sent == 2
        assert len(mockserver.messages) == 2
        assert mockserver.closed == False
        mockserver.end()
        assert mockserver.closed == True




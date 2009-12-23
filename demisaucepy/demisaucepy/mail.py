# email helper, from django
from email.MIMEText import MIMEText
from email.Header import Header
import smtplib, rfc822, logging
from demisaucepy import cfg

# TODO:  extract send_email futher to allow mockserver to be passed in
# TODO:  allow connection to be kept open, external to manage open/close (ie: 
#            not all in one function)
DEFAULT_CHARSET = 'utf-8'
DEFAULT_FROM_EMAIL = cfg.CFG['email_from']
DEFAULT_FROM_NAME = cfg.CFG['email_from_name']
SMTP_USERNAME = cfg.CFG['smtp_username']
SMTP_PASSWORD = cfg.CFG['smtp_password']
SMTP_SERVER = cfg.CFG['smtp_server']
SMTP_PORT = 587 if 'gmail.com' in SMTP_SERVER else 25

class BadHeaderError(ValueError):
    pass

class SafeMIMEText(MIMEText):
    def __setitem__(self, name, val):
        "Forbids multi-line headers, to prevent header injection."
        if '\n' in val or '\r' in val:
            raise BadHeaderError, "Header values can't contain newlines (got %r for header %r)" % (val, name)
        if name == "Subject":
            val = Header(val, DEFAULT_CHARSET)
        MIMEText.__setitem__(self, name, val)

def send_mail(subject, message, recipient_list, from_email=None, 
              fail_silently=False, 
              auth_user=None, 
              auth_password=None):
    """
    Easy wrapper for sending a single message to a recipient list. All members
    of the recipient list will see the other recipients in the 'To' field.
    """
    if not from_email and 'from_email' in cfg.CFG:
        from_email = cfg.CFG['from_email']
    return send_mass_mail([[subject, message, from_email, recipient_list]], 
                          fail_silently, auth_user, auth_password)

class mocksmtp(object):
    def __init__(self,server_address,port):
        self.server_address = server_address
        self.port = port
        self.messages = []
        self.has_started = False
        self.closed = False
        self.connected = False
    
    def start(self):
        self.has_started = True
    
    def login(self,username,password):
        self.connected = True
    
    def send(self,from_email, recipient_list, msg_string):
        self.messages.append((from_email, recipient_list, msg_string))
    
    def end(self):
        self.closed = True
    

class smtphelper(mocksmtp):
    def __init__(self,server_address,port):
        self.server = smtplib.SMTP(server_address, port)
    
    def login(self,username,password):
        self.username = username
        self.password = password
        #before login do start
        self.start()
        self.server.login(username, password)
    
    def send(self,from_email, recipient_list, msg_string):
        self.server.sendmail(from_email, recipient_list, msg_string)
    
    def end(self):
        #if self.username and self.password:
        #    self.server.quit()
        self.server.quit()
    

class gmailsmtphelper(smtphelper):
    def start(self):
        self.server.ehlo()
        self.server.starttls()
        self.server.ehlo()
    
    def end(self):
        self.server.close()
    

def get_smtp_server(smtp_server=SMTP_SERVER, smtp_port=SMTP_PORT):
    "factory to create servers"
    if 'gmail.com' in smtp_server:
        return gmailsmtphelper(smtp_server, smtp_port)
    elif 'mockserver' in smtp_server:
        return mocksmtp(smtp_server, smtp_port)
    else:
        return smtphelper(smtp_server, smtp_port)
    

def send_email(datatuple, fail_silently=False, auth_user=SMTP_USERNAME,
                   auth_password=SMTP_PASSWORD, to_each=False,
                   server=None):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to recipient list. Returns the number of e-mails sent.
    
    Can specifiy to_each, if True will break up recipient list to each user
    
    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    """
    close = False if server else True
    try:
        if not server:
            server = get_smtp_server(SMTP_SERVER, SMTP_PORT)
        
        if auth_user and auth_password:
            server.login(auth_user, auth_password)
    except:
        if fail_silently:
            return
        raise
    num_sent = 0
    def process_send_email(subject, message, from_email, recipient_list):
        from_email = from_email or DEFAULT_FROM_EMAIL
        msg = SafeMIMEText(message, 'plain', DEFAULT_CHARSET)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = ', '.join(recipient_list)
        msg['Date'] = rfc822.formatdate()
        try:
            server.send(from_email, recipient_list, msg.as_string())
            return 1
        except:
            if not fail_silently:
                raise
            return 0
    
    #logging.debug("Unpacking datatuple = %s, %s, %s, %s" % datatuple)
    subject, message, from_email, recipient_list = datatuple
    if not recipient_list:
        pass
    elif to_each and type(recipient_list) == list:
        for email_recipient in recipient_list:
            num_sent += process_send_email(subject, message, from_email, [email_recipient])
    elif type(recipient_list) == list:
        num_sent += process_send_email(subject, message, from_email, recipient_list)
    else:
        num_sent += process_send_email(subject, message, from_email, [recipient_list])
    
    if close:
        try:
            server.end()
        except:
            if fail_silently:
                return
            raise
    
    return num_sent

def send_mail_toeach(datatuple, fail_silently=False, 
                   auth_user=SMTP_USERNAME, 
                   auth_password=SMTP_PASSWORD):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to each recipient list. Returns the number of e-mails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    """
    return send_email(datatuple, fail_silently, auth_user, auth_password, True)

def send_mass_mail(datatuple, fail_silently=False, 
                   auth_user=SMTP_USERNAME, 
                   auth_password=SMTP_PASSWORD):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to each recipient list. Returns the number of e-mails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    """
    return send_email(datatuple, fail_silently, auth_user, auth_password, False)

def main():
    print("Running test .....")

if __name__ == "__main__":
    main()
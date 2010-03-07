# email helper, from django
from email.MIMEText import MIMEText
from email.Header import Header
import smtplib, rfc822, logging
import tornado
from tornado.options import options,define

# TODO:  extract send_email futher to allow mockserver to be passed in
# TODO:  allow connection to be kept open, external to manage open/close (ie: 
#            not all in one function)

define("email_from",default="demisauce@demisauce.org",help="default email from address")
define("smtp_username",default="demisauce@demisauce.org",help="smtp username")
define("smtp_password",default="NOTREAL",help="pwd")
define("smtp_server",default="mockserver.com",help="smtp address, such as smtp.gmail.com")
define("smtp_port",default=25,help="smtp port",type=int)
define("default_from_name",default=None,help="from name that email is sent from, default")

DEFAULT_CHARSET = 'utf-8'

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
    from_email = options.from_email if not from_email else from_email
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
    

def get_smtp_server(smtp_server=None, smtp_port=None):
    smtp_server = options.smtp_server if not smtp_server else smtp_server
    smtp_port = options.smtp_port if not smtp_port else smtp_port
    "factory to create servers"
    if 'gmail.com' in smtp_server:
        return gmailsmtphelper(smtp_server, 587)
    elif 'mockserver' in smtp_server:
        return mocksmtp(smtp_server, smtp_port)
    else:
        return smtphelper(smtp_server, smtp_port)
    

def send_email(datatuple, fail_silently=False, auth_user=None,
                   auth_password=None, to_each=False,
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
            server = get_smtp_server(options.smtp_server, options.smtp_port)
        
        if auth_user and auth_password:
            server.login(auth_user, auth_password)
    except:
        if fail_silently:
            return
        raise
    num_sent = 0
    def process_send_email(subject, message, from_email, recipient_list):
        from_email = from_email or options.email_from
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
                   auth_user=None, 
                   auth_password=None):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to each recipient list. Returns the number of e-mails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    """
    auth_user = options.smtp_username if not auth_user else auth_user
    auth_password = options.smtp_password if not auth_password else auth_password
    return send_email(datatuple, fail_silently, auth_user, auth_password, True)

def send_mass_mail(datatuple, fail_silently=False, 
                   auth_user=None, 
                   auth_password=None):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to each recipient list. Returns the number of e-mails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    """
    auth_user = options.smtp_username if not auth_user else auth_user
    auth_password = options.smtp_password if not auth_password else auth_password
    return send_email(datatuple, fail_silently, auth_user, auth_password, False)

def main():
    print("Running test .....")

if __name__ == "__main__":
    main()
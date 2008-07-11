# emil helper, from django

from pylons import config
from email.MIMEText import MIMEText
from email.Header import Header
import smtplib, rfc822

DEFAULT_CHARSET = 'utf-8'
def default_from_email():
    if 'email_from' in config:
        return config['email_from']
    else:
        return 'guest@demisauce.org'
DEFAULT_FROM_EMAIL = default_from_email()
DEFAULT_FROM_NAME = 'Demisauce Admin'
SMTP_USERNAME = ('smtp_username' in config and config['smtp_username']) or None
SMTP_PASSWORD = ('smtp_password' in config and config['smtp_password']) or None

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
        
def send_mail(subject, message, recipient_list, from_email=DEFAULT_FROM_EMAIL, 
              fail_silently=False, 
              auth_user=SMTP_USERNAME, 
              auth_password=SMTP_PASSWORD):
    """
    Easy wrapper for sending a single message to a recipient list. All members
    of the recipient list will see the other recipients in the 'To' field.
    """
    return send_mass_mail([[subject, message, from_email, recipient_list]], 
                          fail_silently, auth_user, auth_password)

def send_mail_toeach(datatuple, fail_silently=False, 
                   auth_user=SMTP_USERNAME, 
                   auth_password=SMTP_PASSWORD):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to each recipient list. Returns the number of e-mails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    """
    try:
        smtp_server = config.has_key('smtp_server') and config['smtp_server'] or None
        if smtp_server == None or smtp_server == '':
            return
        server = smtplib.SMTP(config['smtp_server'], 25)
        if auth_user and auth_password:
            server.login(auth_user, auth_password)
    except:
        if fail_silently:
            return
        raise
    num_sent = 0
    subject, message, from_email, recipient_list = datatuple
    for to_email in recipient_list:
        from_email = from_email or DEFAULT_FROM_EMAIL
        msg = SafeMIMEText(message, 'plain', DEFAULT_CHARSET)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Date'] = rfc822.formatdate()
        try:
            server.sendmail(from_email, recipient_list, msg.as_string())
            num_sent += 1
        except:
            if not fail_silently:
                raise
            
    try:
        server.quit()
    except:
        if fail_silently:
            return
        raise
    return num_sent

def send_mass_mail(datatuple, fail_silently=False, 
                   auth_user=SMTP_USERNAME, 
                   auth_password=SMTP_PASSWORD):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to each recipient list. Returns the number of e-mails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    """
    try:
        server = smtplib.SMTP(config['smtp_server'], 25)
        if auth_user and auth_password:
            server.login(auth_user, auth_password)
    except:
        if fail_silently:
            return
        raise
    num_sent = 0
    for subject, message, from_email, recipient_list in datatuple:
        if not recipient_list:
            continue
        from_email = from_email or DEFAULT_FROM_EMAIL
        msg = SafeMIMEText(message, 'plain', DEFAULT_CHARSET)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = ', '.join(recipient_list)
        msg['Date'] = rfc822.formatdate()
        try:
            server.sendmail(from_email, recipient_list, msg.as_string())
            num_sent += 1
        except:
            if not fail_silently:
                raise
    try:
        server.quit()
    except:
        if fail_silently:
            return
        raise
    return num_sent

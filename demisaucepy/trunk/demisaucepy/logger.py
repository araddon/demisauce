import threading
import os, logging, sys
LOG_FILE = 'log.log'
ENV = "DJANGO"
try:
    from django.conf import settings
    try:
        LOG_FILE = settings.LOG_FILE
    except Exception:
        try:
            from paste.deploy.converters import asbool
            from pylons import config
            ENV = "PYLONS"
        except ImportError:
            ENV = "OTHER"
except ImportError:
    try:
        from paste.deploy.converters import asbool
        from pylons import config
        ENV = "PYLONS"
        LOG_FILE = config['logfile']
    except ImportError:
        ENV = "OTHER"

def setup_logging():
    """
    http://docs.pylonshq.com/configuration.html#id4

    logging.basicConfig(filename=logfile, mode='at+',
         level=logging.DEBUG,
         format='%(asctime)s, %(name)s %(levelname)s %(message)s',
         datefmt='%b-%d %H:%M:%S')
    """
    if ENV == "PYLONS":
        return
    if LOG_FILE == 'STDOUT': # send to output
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
               #format='%(name)s %(levelname)s %(message)s',
               #format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
               format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
               datefmt='%H:%M:%S')
    else:
        hdlr = logging.FileHandler(LOG_FILE)
        formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s"%(message)s"','%Y-%m-%d %a %H:%M:%S') 
        hdlr.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(hdlr)
        logger.setLevel(logging.NOTSET)
        """logdir = os.path.dirname(os.path.abspath(LOG_FILE))
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        logging.basicConfig(format='%(datefmt)s, %(name)s %(levelname)s %(message)s',
             datefmt='%H:%M:%S')
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
        """
    

#setup_logging()
    



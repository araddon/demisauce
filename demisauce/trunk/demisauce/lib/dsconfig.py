import os, logging
from paste.deploy.converters import asbool
from pylons import config


def setup_logging():
    """
    http://docs.pylonshq.com/configuration.html#id4
    
    logging.basicConfig(filename=logfile, mode='at+',
         level=logging.DEBUG,
         format='%(asctime)s, %(name)s %(levelname)s %(message)s',
         datefmt='%b-%d %H:%M:%S')
    """
    logfile = config['logfile']
    if logfile == 'STDOUT': # special value, used for unit testing
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
               #format='%(name)s %(levelname)s %(message)s',
               #format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
               format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
               datefmt='%H:%M:%S')
    else:
        logdir = os.path.dirname(os.path.abspath(logfile))
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        logging.basicConfig(format='%(datefmt)s, %(name)s %(levelname)s %(message)s',
             datefmt='%H:%M:%S')
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    #setup_thirdparty_logging()

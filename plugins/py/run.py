"""
Runner for Gearman Workers
::
    # see options
    python run.py --help
    # run
    python run.py --config=./path/to/your.conf --logging=error
    
"""
import logging
import tornado
import demisaucepy.options
from demisaucepy import mail # mail options
import demisauce
from tornado.options import options, define
define("asset_root", default="/var/www/ds/static", help="Root Path of images to be saved")

tornado.options.parse_command_line() # must force load of options for metaclass


import dsplugins
from dsplugins import emailer, assets
from gearman import GearmanClient, GearmanWorker
from gearman.task import Task



app = None

def main():
    print("Running Worker .....")
    print("options.logging = %s" % options.logging)
    from demisaucepy import cache_setup
    cache_setup.load_cache()
    #global app
    #app = AppBase()
    logging.info("site_root = %s" % options.site_root)
    logging.info("smtp servers = %s" % options.smtp_server)
    logging.info("cache servers = %s" % options.memcached_servers)
    logging.info("gearman servers 2 = %s" % (options.gearman_servers))
    logging.error("where does this go in supervisord?")
    worker = GearmanWorker(options.gearman_servers)
    worker.register_function("email_send", emailer.email_send)
    worker.register_function("image_resize", assets.image_resize)
    
    worker.work()

if __name__ == "__main__":
    main()
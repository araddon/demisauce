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
import demisaucepy
from demisaucepy import mail
import dsplugins
from dsplugins import emailer, assets
from tornado.options import options, define
from gearman import GearmanClient, GearmanWorker
from gearman.task import Task

define("asset_root", default="/var/www/ds/static", help="Root Path of images to be saved")

app = None

def main():
    print("Running Worker .....")
    tornado.options.parse_command_line()
    print("options.logging = %s" % options.logging)
    
    #global app
    #app = AppBase()
    logging.info("site_root = %s" % options.site_root)
    logging.info("smtp servers = %s" % options.smtp_server)
    logging.info("gearman servers 2 = %s" % (options.gearman_servers))
    logging.error("where does this go in supervisord?")
    worker = GearmanWorker(options.gearman_servers)
    worker.register_function("email_send", emailer.email_send)
    worker.register_function("image_resize", assets.image_resize)
    
    worker.work()

if __name__ == "__main__":
    main()
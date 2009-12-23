"""
Runner for Gearman Workers
::
    
    python run.py --config=./../../demisauce.conf --logging=error
    
"""
import logging
import tornado
from demisauce import AppBase
from tornado.options import options
from gearman import GearmanClient, GearmanWorker
from gearman.task import Task


app = None

def main():
    print("Running Worker .....")
    tornado.options.parse_command_line()
    
    global app
    app = AppBase()
    
    from demisauce.gearman import assets, emailworker
    logging.info("smtp servers = %s" % options.smtp_server)
    logging.info("gearman servers 2 = %s" % (options.gearman_servers))
    logging.error("where does this go in supervisord?")
    worker = GearmanWorker(options.gearman_servers)
    worker.register_function("email_send", emailworker.email_send)
    worker.register_function("image_resize2", assets.image_resize)
    
    worker.work()

if __name__ == "__main__":
    main()
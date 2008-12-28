#!/bin/sh -e
DEMISAUCE_HOME=$1
cd $DEMISAUCE_HOME
case "$1" in
  start)
    paster serve --daemon --pid-file=demisauce.pid production.ini start
    ;;
  stop)
    paster serve --daemon --pid-file=demisauce.pid production.ini stop
    ;;
  restart)
    paster serve --daemon --pid-file=demisauce.pid production.ini restart
    ;;
  force-reload)
    paster serve --daemon --pid-file=demisauce.pid production.ini restart
    /etc/init.d/apache2 restart
    ;;
  *)
    echo $"Usage: $0 {start|stop|restart|force-reload}"
    exit 1
esac

exit 0

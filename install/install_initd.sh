#!/bin/sh -e

. /lib/lsb/init-functions
 
#------------------------------------------------------------------------------
#                               Consts
#------------------------------------------------------------------------------
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
NAME=demisauce
DEMISAUCE_HOME="/home/demisauce/ds/current_web/"
DESCRIPTION="Demisauce Pylons/Paster app"
PIDSPATH=$DEMISAUCE_HOME
PS=$NAME              #the process, which happens to be the NAME
PIDFILE=$NAME.pid     #pid file
RUNAS=root            #user to run as
SCRIPT_OK=0           #ala error codes
SCRIPT_ERROR=1        #ala error codes
TRUE=1                #boolean
FALSE=0               #boolean

#------------------------------------------------------------------------------
#                               Functions
#------------------------------------------------------------------------------
pidof_daemon() {
    PIDS=`pidof $PS` || true
 
    [ -e $PIDSPATH/$PIDFILE ] && PIDS2=`cat $PIDSPATH/$PIDFILE`
 
    for i in $PIDS; do
        if [ "$i" = "$PIDS2" ]; then
            return 1
        fi
    done
    return 0
}
getPSCount() {
  return `pgrep -f $PS | wc -l`
}
 
isRunning(){
  pidof_daemon
  PID=$?
 
  if [ $PID -gt 0 ]; then
    return 1
        else
                return 0
        fi
}
start() {
        isRunning
        isAlive=$?
        if [ "${isAlive}" -eq $TRUE ]; then
            # ok, im using cron to keep running, so ignore this
            return 0
        else
            log_daemon_msg "Starting $DESCRIPTION"
            paster serve --daemon --pid-file=$PIDFILE production.ini start
            chmod 400 $DEMISAUCE_HOME/$PIDFILE
            log_end_msg $SCRIPT_OK
        fi
}



cd $DEMISAUCE_HOME
case "$1" in
  start)
    start
    ;;
  stop)
    paster serve --daemon --pid-file=demisauce.pid production.ini stop
    ;;
  restart)
    paster serve --daemon --pid-file=demisauce.pid production.ini restart
    ;;
  force-reload)
    paster serve --daemon --pid-file=demisauce.pid production.ini restart
    ;;
  *)
    echo $"Usage: $0 {start|stop|restart|force-reload}"
    exit 1
esac

exit 0

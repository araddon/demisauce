This is the main installer and it is assumed you are doing a server install, or on a VMWare if this is a server and not development as that is the recommended install.

Installation and Setup
======================
This installation uses Ubuntu JEOS

Get `Ubuntu JEOS <http://www.ubuntu.com/products/whatisubuntu/serveredition/jeos>`_ and start the install by doing updates and adding SSH and wget::

    apt-get update
    apt-get install openssh-server wget

Get `Demisauce Installer <http://github.com/araddon/demisauce/raw/master/install/install.sh>`_  using wget or just copy text.

Copy to /tmp/install.sh and run::

    cd /tmp
    wget http://github.com/araddon/demisauce/raw/master/install/install.sh
    wget http://github.com/araddon/demisauce/raw/master/install/install_demisauce.sh
    chmod +x install.sh 
    ./install.sh



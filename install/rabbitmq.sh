#wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
cd /tmp
cp /etc/apt/sources.list /etc/apt/sources.list.bak.demisauce

cat <<EOF >>/etc/apt/sources.list

# rabbitmq source repo
deb http://www.rabbitmq.com/debian/ testing main
EOF

wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
apt-key add rabbitmq-signing-key-public.asc
apt-get update
sudo apt-get install --yes --force-yes -q rabbitmq-server

#wget http://www.apache.org/dist/qpid/M4/qpid-python-M4.tar.gz
#tar -xzvf qpid-python-M4.tar.gz
#cd qpid-M4/python
#python setup.py install
easy_install http://pypi.python.org/packages/source/a/amqplib/amqplib-0.6.tgz



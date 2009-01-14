#!/usr/bin/env python

#  This assumes that your EC2 is in .ec2
#
#  python start_ec2.py amazon_access_key secret_access_key

import sys, os
from ec2 import EC2
import threading, time

AMI = "ami-1c5db975" # Ubuntu 8.04 small  http://alestic.com/
KEY_PAIR = "gsg-keypair"
EC2_BIN = "~/.ec2/bin/" # Amazon EC2 system scripts directory
DOT_EC2 = "~/.ec2/" # users' keys directory
SECURITY_GROUP_NAME = "default"
here = os.path.abspath(os.path.dirname(__file__))
DS_INSTALL_FILE = "%s/install.sh" % (here)

def test_demisauce(access_key_id, secret_access_key):
    """start demisauce image"""
    conn = EC2.AWSAuthConnection(access_key_id, secret_access_key)
    print "----- listing images -----"
    print conn.describe_images()
    print "----- listing instances -----"
    print conn.describe_instances()
    print "----- listing keypairs (verbose mode) -----"
    conn.verbose = True
    print conn.describe_keypairs()

def start_ds_server(access_key_id, secret_access_key):
    conn = EC2.AWSAuthConnection(access_key_id, secret_access_key)
    print('after connection, about to start instance')
    run_response =  conn.run_instances(AMI,keyName=KEY_PAIR,availabilityZone='us-east-1a')
    instance_id = run_response.instanceId
    print('about to sleep to wait for 60 secs, then describe instances to get address')
    print("You must type Yes for adding RSA fingerprint")
    time.sleep(60)
    instance_info = conn.describe_instances([instance_id])
    print("Amazon InstanceId= %s" % (instance_info.instanceId))
    print('Amazon dnsName = %s' % (instance_info.dnsName))
    # lets get your amazon keypair up onto the instance: 
    os.system("scp -i ~/.ec2/id_rsa-%s ~/.ec2/{cert,pk}-*.pem root@%s:/mnt/" % (KEY_PAIR,instance_info.dnsName))
    # move up the demisauce install file
    os.system("scp -i ~/.ec2/id_rsa-%s %s root@%s:/mnt/" % (KEY_PAIR,DS_INSTALL_FILE,instance_info.dnsName))
    # ssh command
    ssh_cmd = 'ssh -i %sid_rsa-%s root@%s' % (DOT_EC2,KEY_PAIR,instance_info.dnsName)
    print("""Run these commands on your local machine
    ~/.ec2/ec2-create-volume -z us-east-1a -s 10
    ~/.ec2/ec2-describe-volumes vol-VVVV1111
    ec2-attach-volume -d /dev/sdh -i i-IIII1111 vol-VVVV1111
    
    
    # ssh into amazon server at:
    %s
    # then run these from amazon machine after ssh'ing in
    chmod +x /mnt/install.sh
    /mnt/install.sh
    """ % ssh_cmd)
    print("Then your Demisauce server is available at http://%s" % (instance_info.dnsName))
    #os.system(ssh_cmd)


def bundle_ds_server(aws_account_id):
    """Starts a Demisauce EC2 image and bundles it"""
    #ec2-bundle-vol -d /mnt -k /mnt/pk-*.pem -c /mnt/cert-*.pem -u AWSAccountID -r i386 -p demisaucebase
    #ec2-upload-bundle -b demisauce -m /mnt/demisaucebase.manifest.xml -a <aws-access-key-id> -s <aws-secret-access-key> 
    # on local computer:
    #ec2-register demisauce/demisaucebase.manifest.xml
    pass


if __name__=='__main__':
    if len(sys.argv) < 4:
        print 'usage:   python start_ec2.py (start|bundle) access_key secrete_access_key'
    else:
        method = sys.argv[1]
        access_key, secrete_access_key = sys.argv[2], sys.argv[3]
        if method == 'test':
            test_demisauce(access_key, secrete_access_key)
        elif method == 'start':
            start_ds_server(access_key, secrete_access_key)
        elif method == 'bundle':
            start_ds_server(access_key, secrete_access_key)
        else:
            print('Command:  %s not recognized' % method)


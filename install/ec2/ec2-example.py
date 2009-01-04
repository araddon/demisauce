#!/usr/bin/env python

#  This software code is made available "AS IS" without warranties of any
#  kind.  You may copy, display, modify and redistribute the software
#  code either by itself or as incorporated into your code; provided that
#  you do not remove any proprietary notices.  Your use of this software
#  code is at your own risk and you waive any claim against Amazon Web
#  Services LLC or its affiliates with respect to your use of this software
#  code. (c) 2006 Amazon Web Services LLC or its affiliates.  All rights
#  reserved.

import sys
import EC2

AWS_ACCESS_KEY_ID = '<INSERT YOUR AWS ACCESS KEY ID HERE>'
AWS_SECRET_ACCESS_KEY = '<INSERT YOUR AWS SECRET ACCESS KEY HERE>'
# remove these next two lines as well, when you've updated your credentials.
print "update %s with your AWS credentials" % sys.argv[0]
sys.exit()

SECURITY_GROUP_NAME = "ec2-example-rb-test-group"

conn = EC2.AWSAuthConnection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

print "----- listing images -----"
print conn.describe_images()

print "----- listing instances -----"
print conn.describe_instances()

print "----- creating a security group -----"
print conn.create_securitygroup(SECURITY_GROUP_NAME, "ec-example.rb test group")

print "----- listing security groups -----"
print conn.describe_securitygroups()

print "----- deleting a security group -----"
print conn.delete_securitygroup(SECURITY_GROUP_NAME)

print "----- listing keypairs (verbose mode) -----"
conn.verbose = True
print conn.describe_keypairs()


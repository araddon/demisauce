"""
Demisauce
===========

`Demisauce
<http://www.demisauce.org>`_ is a set of web services to be utilized
within other applications.  Instead of building on top of a content management
framework etc, you can utilize these web services.  See more at the web site.

* Content Management:  Get Chunks of Content (XML, Html) for inclusion
  in the output of your pages using your templating.

* Email templates:  get email template (XML) for sending of emails.

* Polls:

* Comment System


Download and Installation
-------------------------

Demisauce can be installed with `Easy Install
<http://peak.telecommunity.com/DevCenter/EasyInstall>`_ by typing::

    > easy_install demisaucepy

"""
from setuptools import setup, find_packages
import sys, os

version = '0.1.0'

setup(name='demisaucepy',
      version=version,
      description="Python library to Demisauce",
      long_description="""
Demisauce
===========

`Demisauce
<http://demisauce.googlecode.com>`_ is a set of web services to be utilized
within other applications.  Instead of building on top of a content management
framework etc, you can utilize these web services.

* Content Management:  Get Chunks of Content (XML, Html) for inclusion
  in the output of your pages using your templating.

* Email templates:  get email template (XML) for sending of emails.

* Administration pages to edit email, content items for use in your app.


Download and Installation
-------------------------

Demisauce can be installed following these `instructions
<http://code.google.com/p/demisauce/wiki/InstallationInstructions>`_

""",
    classifiers=["Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ], 
    keywords='python',
    author='Aaron Raddon',
    author_email='',
    url='http://demisauce.googlecode.com/',
    download_url='http://demisauce.googlecode.com/files/demisaucepy-0.1.0.tar.gz',
    install_requires=["elementtree>=1.1","nose>=0.10.4"],
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples']),
    include_package_data=True,
    test_suite='nose.collector',
    zip_safe=False,
    entry_points="""
    # -*- Entry points: -*-
    """,
)


from setuptools import setup, find_packages
import sys, os

version = '0.1.1'

setup(name='demisaucepy',
      version=version,
      description="Python library to Demisauce",
      long_description="""
Demisauce
===========

`Demisauce
<http://www.demisauce.com>`_ is a set of web services to be utilized
within other applications.  Instead of building on top of a framework
you can utilize these web services as components in your app.  Or get the 
`source code <http://http://github.com/araddon/demisauce/tree/master>`_

* Email templates:  get email template (XML) for sending of emails.

* Polls:  Simple embeddable polls, embed on server side with caching
  for high performance.

* Comment System:  embed comments related to your articles, books, items, etc

* Activity Graphs and tracking.

* Help and feedback system.


Download and Installation
-------------------------

Demisauce can be installed with `Easy Install
<http://peak.telecommunity.com/DevCenter/EasyInstall>`_ by typing::

  > easy_install demisaucepy

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
    url='http://github.com/araddon/demisauce',
    download_url='http://demisauce.googlecode.com/files/demisaucepy-0.1.1.tar.gz',
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

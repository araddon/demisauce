from paver.defaults import *

#from paver.release import setup_meta

import paver.doctools

#import paver.virtual
import paver.setuputils

options(
    setup=Bunch(
        name="demisauce",
        description='Shared Services for use within your application via rest',
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
        version="0.1.0",
        author="Aaron Raddon",
        classifiers=["Development Status :: 2 - Pre-Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python",
            "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
        url='http://demisauce.googlecode.com',
        install_requires=["Pylons>=0.9.6","gdata>=1.0",'sqlalchemy>=0.4.6',
            'demisaucepy>=0.0.2','genshi>=0.5','tempita','simplejson'],
        
        include_package_data=True,
        test_suite='nose.collector',
        packages=['demisauce'],
        package_data={'demisauce': ['i18n/*/LC_MESSAGES/*.mo']},
        #message_extractors = {'demisauce': [
        #        ('**.py', 'python', None),
        #        ('templates/**.mako', 'mako', None),
        #        ('public/**', 'ignore', None)]},
        entry_points="""
        [paste.app_factory]
        main = demisauce.config.middleware:make_app

        [paste.paster_command]
        dataload = demisauce.websetup:SetupTestData
    
        [paste.app_install]
        main = demisauce.lib.dsinstaller:DemisauceInstaller
        """
    ),
    sphinx=Bunch(
            builddir=".build"
    )
)

options.setup.package_data=setuputils.find_package_data("demisauce", package="demisauce",
                                                only_in_packages=False)

@task
@needs('paver.doctools.html')
def htmlnot():
    """Build the docs and put them into our package."""
    builtdocs = path("docs") / options.sphinx.builddir / "html"
    destdir = path('htmldocs')
    destdir.rmtree()
    builtdocs.move(destdir)
    




try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='demisauce',
    version="0.1.0",
    description='Shared Services for use within your application via rest',
    author='Aaron Raddon',
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
    url='http://demisauce.googlecode.com',
    install_requires=["Pylons==0.9.6.2",'sqlalchemy==0.4.8',
        'demisaucepy>=0.0.2','tempita','simplejson'],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
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
    """,
)

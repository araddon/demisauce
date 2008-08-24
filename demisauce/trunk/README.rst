Demisauce is the main web application that hosts web services for use by
    other applications.   The library applications for consuming these web 
    services are in other projects, depending on which technology you need.
    
Installation and Setup
======================
Requires Pylons, and either MySQL or SqlLite


Install ``demisauce`` using subversion::

    http://code.google.com/p/demisauce/source

Make a config file as follows::

    paster make-config demisauce config.ini

Tweak the config file as appropriate and then setup the application,
    there is a development_ini.sample file which should be close to
    what you need.

    paster setup-app config.ini

the paster "setup-app" will output a "site key" (an api key to update into your
    ini setting).  It will also give you your username, password

    paster serve --reload development.ini
    
Development
======================
After making changes to the model, if you are using SQLAlchemy to 
    create db, you can write changes to db using:  (runs websetup.py setup_config())
    
    paster setup-app development.ini
    
After making changes to the model, if you are using SQLAlchemy to 
    create db, you can write changes to db using:  (runs websetup.py setup_config())

    paster setup-app development.ini
    
TESTING
======================
Use's nosetest, see full `nosetest documentation <http://www.somethingaboutorange.com/mrl/projects/nose/>`_

To run tests::

    nosetests -s
    
run just one file worth of tests::

    nosetests -s  test_loads.py   
gets all folders, not just tests::

    nosetests -w ../  --with-doctest -v 
    
includes test folder lking for doctests::

    nosetests --with-doctest --doctest-tests
        
    OR
    
    python setup.py test
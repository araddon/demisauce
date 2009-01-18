Demisauce is the main web application that hosts web services for use by
    other applications.   The library applications for consuming these web 
    services are in other projects, depending on which technology you need.
    
Installation and Setup
======================
Requires Pylons, and either MySQL or SqlLite


Install _Demisauce: http://github.com/araddon/demisauce/tree/master using git


Make a config file as follows::

    paster make-config demisauce development.ini

Tweak the config file as appropriate for your database and settings.
Also, you can run command line tool to update admin email/pwd and host url::

    paster setup-app development.ini
    paster updatesite -p yourpwd -e sysadmin@demisauce.org -h http://yoursite.com -i development.ini

the paster "setup-app" will output a "site key" (an api key to update into your
ini setting).  It will also give you your username, password::

    paster serve --reload development.ini

Development
======================
After making changes to the model, if you are using SQLAlchemy to 
create db, you can write changes to db using:  (runs websetup.py setup_config())::
    
    paster setup-app development.ini
    
To delete table's, and reload the fixture one table (or set of 
related tables such as poll's).  

Default ini is library_test.ini::

    paster dataload -c person -i development.ini
    
    OR
    
    paster dataload -c site

TESTING
======================
Use's nosetest, see full `nosetest documentation<http://www.somethingaboutorange.com/mrl/projects/nose/>`_

To run tests::

    nosetests -s

run just one file worth of tests::

    nosetests -s  test_loads.py  

gets all folders which may have doctest, not just tests::

    nosetests -w ../  --with-doctest -v 

includes test folder for doctests::

    nosetests --with-doctest --doctest-tests
    
    OR
    
    python setup.py test
    
to load a fresh set of data for testing::
    
    $paster setup-app library_test.ini
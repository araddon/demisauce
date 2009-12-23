try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='demisauce',
    version="0.1.1",
    description='Integration Appliance, common integration tasks done and pre-installed',
    author='Aaron Raddon',
      long_description="""
Demisauce
===========

`Demisauce
<http://www.github.com/araddon/demisauce>`_ is an integration appliance, 
pre-configured integration services Gearman, SOLR, logging, Redis, together
with services such as Add user.


""",
    classifiers=["Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ], 
    url='http://demisauce.googlecode.com',
    install_requires=['sqlalchemy==0.5.6',
        'demisaucepy>=0.0.2','tempita',
        'webhelpers'],
    py_modules = ['app','manage'],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'demisauce': ['i18n/*/LC_MESSAGES/*.mo']},
)

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

version = '0.1.1'

setup(name='dsplugins',
      version=version,
      description="Python Plugins to Demisauce",
      long_description="""
Demisauce
===========
`Demisauce <http://www.demisauce.com>`_ is an integration appliance, a network
plugin system that provides integrations with systems:  remote (Google Apps, 
Twitter, Wordpress) and local (Gearman, Memcached, Wordpress).  

These are the plugin's to the other systems.

Download and Installation
-------------------------

see Github:   http://github.com/araddon/demisauce/

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
    install_requires=[],
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples']),
    include_package_data=True,
    test_suite='nose.collector',
    zip_safe=False,
)

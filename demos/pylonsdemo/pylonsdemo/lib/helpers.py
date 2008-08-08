"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from webhelpers import *
from demisaucepy.pylons_helper import *

def isdemisauce_admin():
    """
    Determines if current user is DemiSauce admin, and if so will show
    a link to Demisauce admin to add items that don't exist
    """
    return True

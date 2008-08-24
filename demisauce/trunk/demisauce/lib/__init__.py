import re


def slugify(name):
    """
    Convert's a string to a slugi-ifyed string
    
    >>> lib.slugify("aaron's good&*^ 89 stuff")
    'aarons-good-stuff'
    """
    name = re.sub('( {1,100})','-',name)
    name = re.sub('[^a-z\-]','',name)
    name = re.sub('(-{2,50})','-',name)
    return name

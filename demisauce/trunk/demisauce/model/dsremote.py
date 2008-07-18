"""
Special test for testing a remote aggregate object
"""
class DSA(object):
    creation_counter = 0
    def __init__(self, name=None):
      self.name = name
      print 'my name = %s' % name
      DSA.creation_counter += 1
  
    def __getitem__(self,attrname):
        """
        get atribute
        """
        print 'in __getitem__ %s' % attrname
     
class Test(object):
    key = DSA('comment')
    def __getitem__(self,attrname):
        """
        get atribute
        """
        print 'in DSA__getitem__ %s' % attrname
    

class DemisauceAggregator(object):
    def __init__(self, *args, **kwds):
        self.__isdirty = False
        #DBModel.__init__(self, parent=None, key_name=None, _app=None, **kwds)
    
    def __getattr__(self,attrname):
        """
        get attribute
        """
        print 'in __get_attr %s' % attrname
        if (attrname.find('_') != 0):
            if hasattr(self,'_' + attrname):
                curval = getattr(self,'_' + attrname)
                if curval != value:
                    self.__isdirty = True
                    if hasattr(self,attrname + '_onchange'):
                        getattr(self,attrname + '_onchange')(curval,value)
        
        #DBModel.__setattr__(self,attrname,value)

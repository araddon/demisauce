""" 
This is an Xml to Python object de-serializer.  It produces python objects of 
very pure object syntax matching what you would expect from xml.  

Example:

    xml_str = '''
    <emails>
        <email id="32" key="GoalswarmNodeInvite">
            <subject>Goalswarm Node Invite</subject>
            <empty></empty>
            <from_email>goalswarm@notnow.com</from_email>
            <from_name>Goalswarm Invites</from_name>
            <to>test@demisauceforspam.org</to>
            <template>
                Welcome to Goalswarm.  has sent you an invite to participate in brainstorming together on ##nodename##.
            </template>
        </email>
        <email id="12" key="PasswordReset">
            <subject>The Goalswarm Password you requested</subject>
            <from_email>goalswarm@notnow.com</from_email>
            <from_name>Goalswarm</from_name>
            <to>test@demisauceforspam.org</to>
            <template><![CDATA[
             You have requested to reset your password on http://www.Goalswarm.com on ##nodename##.  
             ]]>               
            </template>
        </email>
    </emails>
        '''
    emails = XMLNode(xml_str)
    print "emails.email = %s" % emails.email            # [<xmlnode>,<xmlnode>]
    print "email0.id = %s" % emails.email[0].id         # 32
    print "email0.id = %s" % emails.email[0].attr['id'] # 32
    print "email0.empty = %s" % emails.email[0].empty   #    None, but shouldn't blow up
    print "email0.to = %s" % emails.email[0].to         # test@demisauceforspam.org
    print "email0.subject = %s" % emails.email[0].subject
    print "email0.template = %s" % emails.email[0].template.strip()
    print "email1.template = %s" % emails.email[1].template.strip()
    print "test out iterations of fully qualified emails.email"
    for email in emails.email:
        print 'email id= %s, subject = %s' % (email.id,email.subject)
    print "test out iterations of for email in emails:  # cheater"
    for email in emails:
        print 'email id= %s, subject = %s' % (email.id,email.subject)

    emails.email = [<__main__.XMLNode instance at 0x00C16120>, <__main__.XMLNode instance at 0x00C1F7D8>]
    email0.id = 32
    email0.id = 32
    email0.empty = None
    email0.to = test@demisauceforspam.org
    email0.subject = Goalswarm Node Invite
    email0.template = Welcome to Goalswarm.  has sent you an invite to participate in brainstorming together on ##nodename##.
    email1.template = You have requested to reset your password on http://www.Goalswarm.com on ##nodename##.
    test out iterations of fully qualified emails.email
    email id= 32, subject = Goalswarm Node Invite
    email id= 12, subject = The Goalswarm Password you requested
    test out iterations of for email in emails:  # cheater
    email id= 32, subject = Goalswarm Node Invite
    email id= 12, subject = The Goalswarm Password you requested

"""
import elementtree.ElementTree as ET
from elementtree.ElementTree import XML

__all__ = ('XMLNode', )


def needs_child_node(element):
    """
    checks an xml element to see if it needs a
    child XMLNode
    """
    pass

class XMLNode:
    """
    generic class for holding an XML node, turns xml syntax
    into native object syntax:
    """
    _builtins = ['elementName','elementText','attr','elcount','dom','_xmlhash','_itercount','datefield']
    def __init__(self,xmlinput):
        """
        Construct a python object from an xml string or from ElementTree element
        """
        self.elcount = 0
        self.elementName = ""
        self.elementText = ""
        self.attr = {}
        self._xmlhash = {}
        self._itercount = 0
        
        
        if type(xmlinput) is str:
            self.dom = XML(xmlinput)
            self.__parseXMLElement__(self.dom)
        else:
            self.dom = xmlinput
            self.__parseXMLElement__(self.dom)
    
    def __len__(self):
        if self.elcount == 1:
            for k in self._xmlhash.keys():  
                if type(self._xmlhash[k]) == list:
                    return len(self._xmlhash[k])
                else:
                    return 1
                    
        return self.elcount
    
    def datefield(self,field):
        """
        returns a string field formated as a date
        """
        # what?  there has to be an easier way than this
        c = self._xmlhash[field]    
        il = [int(i) for i in [c[0:4],c[5:7],c[8:10],c[11:13],c[14:16],c[17:19],c[20:22]]]
        from datetime import datetime
        d = datetime(il[0],il[1],il[2],il[3],il[4],il[5])
        return d
    
    def is_text_element(self):
        """determines if current node is a child-less text"""
        if self.elcount > 1:
            return False
        elif self.elcount == 1:
            k = self._xmlhash.keys()[0]
            if type(self._xmlhash[k]) == XMLNode:
                return False
            elif type(self._xmlhash[k]) == str:
                return True
        else:
            return False
    
    def __getitem__(self, key):
        """
        iterator and more
        """
        if type(key) is int:  
            if self.elcount == 1:  # only one, so easy to choose which they seek
                for k in self._xmlhash.keys(): 
                    #print 'in __getitem__ %s  %s' % (key, self._xmlhash[k])
                    if type(self._xmlhash[k]) == list:
                        return self._xmlhash[k][key]
                    else:
                        # similar to case below, the user thought was
                        # a list but only one item
                        if key > 0:
                            raise StopIteration
                        return self._xmlhash[k]
            else:  
                # this case occurs when some xml item which is normally a list only
                # has a single item, so lets return self, and kill iteration after this
                if key > 0:
                    raise StopIteration
                return self
        
        for k in self.__dict__.keys():
            #print '__dict__.k = %s' % (k)
            if key == k:
                return self.__dict__[k]
        
        return self.__dict__[key]
    
    def __setattr__(self,name,value):
        """
        Override the set attr method
        """
        #print 'in setattr   name = %s   val = %s' % (name,value)
        if name in XMLNode._builtins:
            self.__dict__[name] = value
        elif not name in self.__dict__:
            self.elcount += 1
            self.__dict__[name] = value
            self._xmlhash[name] = value
            #print 'adding el/attribute %s  val=%s' % (name,value)
        elif type(self.__dict__[name]) == list:
            self.__dict__[name].append(value)
            #print 'appending to list %s  val=%s' % (name,value)
        else:
            # only 1 currently, convert to list
            #print 'creating list %s' % name
            self.__dict__[name] = [self.__dict__[name],value]
            self._xmlhash[name] = self.__dict__[name]
    
    def __parseXMLElement__(self,element):
        """
        Recursive call to process this XMLNode.
        """
        self.elementName = element.tag
        # add element attributes as attributes to this node
        if element.keys():
            for name, value in element.items():
                self.attr[name] = value
                self.__setattr__(name, value)
        
        for child in element.getchildren():
            if (len(child.keys()) + len(child._children)) > 1:  # elms + att's 
                #print 'yes, longer = %s' % (len(child.keys()) + len(child._children))
                x = XMLNode(child)
                self.__setattr__(child.tag, x)
            elif len(child._children) == 1:
                #print '203 tag=%s  len children > 0  %s ' % (child.tag,len(child._children),)
                x = XMLNode(child)
                # is this still needed?
                if x.is_text_element():
                    #print 'tag=%s elcount = 1, elementName=%s' % (child.tag,x.elementName)
                    childtext = child.text.strip()
                    if childtext == '' or childtext == None:
                        #for c2 in child.getchildren():
                        #    print dir(c2)
                        self.__setattr__(child.tag, x.elementText)
                else:
                    #print '214 tag=%s, x.elcount=%s' % (child.tag,x.elcount)
                    self.__setattr__(child.tag, x)
            elif len(child._children) == 0:
                self.__setattr__(child.tag, child.text)
                self.elelmentText = child.text
                test = '''
                #print 'tag=%s   text=%s' % (child.tag, child.text)
                if not len(child._children) > 0:
                    print 'child.text tag=%s   %s   ' % (child.tag,child.text)
                    print 'attrs = %s' % (self.attr)
                    self.__setattr__(child.tag, child.text)
                    self.elelmentText = child.text
                elif len(child._children) > 0:
                    #print 'tag=%s  len children > 0  %s ' % (child.tag,len(child._children),)
                    x = XMLNode(child)
                    # is this still needed?
                    if x.is_text_element():
                        print 'tag=%s elcount = 1, elementName=%s' % (child.tag,x.elementName)
                        childtext = child.text.strip()
                        if childtext == '' or childtext == None:
                            #for c2 in child.getchildren():
                            #    print dir(c2)
                            self.__setattr__(child.tag, x.elementText)
                    else:
                        print '198 tag=%s, x.elcount=%s' % (child.tag,x.elcount)
                        self.__setattr__(child.tag, x)
                    '''
            else:
                #print '239:  %s   %s  %s' % (len(child.keys()),len(child._children), child.text)
                print 'in else of children, shouldnt happen tag=%s'  % (child.tag)
        
    

if __name__=='__main__':
    xml_str = '''
    <emails>
        <email id="32" key="GoalswarmNodeInvite">
            <subject>Goalswarm Node Invite</subject>
            <empty></empty>
            <from_email>goalswarm@notnow.com</from_email>
            <from_name>Goalswarm Invites</from_name>
            <to>test@demisauceforspam.org</to>
            <template>
                Welcome to Goalswarm.  has sent you an invite to participate in brainstorming together on ##nodename##.
            </template>
        </email>
        <email id="12" key="PasswordReset">
            <subject>The Goalswarm Password you requested</subject>
            <from_email>goalswarm@notnow.com</from_email>
            <from_name>Goalswarm</from_name>
            <to>test@demisauceforspam.org</to>
            <template><![CDATA[
             You have requested to reset your password on http://www.Goalswarm.com on ##nodename##.  
             ]]>               
            </template>
        </email>
    </emails>
        '''
    emails = XMLNode(xml_str)
    #print dir(emails)
    print "emails.email = %s" % emails.email            # [<xmlnode>,<xmlnode>]
    print "email0.id = %s" % emails.email[0].id         # 32
    print "email0.id = %s" % emails.email[0].attr['id']      # 32
    print "email0.empty = %s" % emails.email[0].empty   #    None, but shouldn't blow up
    print "email0.to = %s" % emails.email[0].to         # test@demisauceforspam.org
    print "email0.subject = %s" % emails.email[0].subject
    print "email0.template = %s" % emails.email[0].template.strip()
    print "email1.template = %s" % emails.email[1].template.strip()
    print "test out iterations of fully qualified emails.email"
    for email in emails.email:
        print 'email id= %s, subject = %s' % (email.id,email.subject)
    print "test out iterations of for email in emails:  # cheater"
    for email in emails:
        print 'email id= %s, subject = %s' % (email.id,email.subject)
        
    xml_str = '''
        <poll id="1">
            <name>test poll</name>
            <created>2008-06-30 23:14:45.115906</created>
            <allow_anonymous>False</allow_anonymous>
            <questions>
                <question id="1" type="radiowtext">
                    <question>why is chocolate good?</question>
                    <options>
                        <option id="1" type="radio">because its sweet!</option>
                        <option id="2" type="radio">because its bitter!</option>
                        <option id="3" type="text">Other</option>
                    </options>
                </question>
                <question id="2" type="radiowtext">
                    <question>why is chocolate good?</question>
                    <options>
                        <option id="4" type="radio">because its sweet!</option>
                    </options>
                </question>
            </questions> 
        </poll>
            '''
    polls = XMLNode(xml_str)
    print "polls.id = %s, name=%s" % (polls.id,polls.name)   
    print "polls.questions = %s" % (polls.questions)
    print 'type polls = %s' % type(polls.questions)     
    for q in polls.questions:
        print q.elementName
        print q.type
        print q.question
        #print dir(q.options.option[0])
        
    xml_str = '''<?xml version="1.0" encoding="utf-8" ?>
    <demisauce>
        <person id="1" user_uniqueid="02199e1f544027da7b7d39b5c865c7c51e460987">
            <displayname>Sys Admin @Demisauce</displayname>
            <created>2008-06-30 23:14:45.105529</created>
            <email>sysadmin@demisauce.org</email>
            <hashedemail>0c0342d8eb446cd7743c3f750ea3174f</hashedemail>
            <url>http://yourapp.wordpress.com</url>

            <authn>local</authn>
            <groups>
                <group id="3">Updated Group Name</group>
            </groups> 
        </person>
    </demisauce>'''
    demisauce = XMLNode(xml_str)
    person = demisauce.person
    print "persons.id = %s, name=%s" % (person.id,person.displayname)   

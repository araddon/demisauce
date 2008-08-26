"""
Tests for the XMLnode element
"""
from demisaucepy.tests import *
from demisaucepy import XMLNode
from demisaucepy import demisauce_ws_get
from demisaucepy import cfg

class TestXmlNode(TestDSBase):
    dsitem = None
    def test_xmlnode_lists(self):
        """
        Test the xml nodes List Capabilities
        if it returns a list, or if you thought there was
        going to be a list, but only a single element was returned
        """
        xml_str = '''
    <emails>
        <email id="32" key="GoalswarmNodeInvite">
            <subject>Goalswarm Node Invite</subject>
            <empty></empty>
            <from_email>goalswarm@notnow.com</from_email>
        </email>
        <email id="12" key="PasswordReset">
            <subject>The Goalswarm Password you requested</subject>
            <from_email>goalswarm@notnow.com</from_email>
        </email>
    </emails>
        '''
        nodes = XMLNode(xml_str)
        assert nodes
        assert hasattr(nodes,'email')
        # since email is the only child of nodes, we should be able to iterate the parent
        nodes2 = [n for n in nodes]
        assert len(nodes2) == 2
        assert nodes[0].subject == 'Goalswarm Node Invite'
        # also, node.email should be iterable (should be the same)
        nodes3 = [n for n in nodes.email]
        assert len(nodes3) == 2
        assert nodes3[0].subject == 'Goalswarm Node Invite'
        # or using slicing
        node1 = nodes.email[0]
        assert str(node1.__class__) == 'demisaucepy.xmlnode.XMLNode'
        assert node1.subject == 'Goalswarm Node Invite'
        assert hasattr(node1,'subject')
        xml_str2 = '''
    <emails>
        <email id="12" key="PasswordReset">
            <subject>Goalswarm Node Invite</subject>
            <from_email>goalswarm@notnow.com</from_email>
        </email>
    </emails>
        '''
        nodes4 = XMLNode(xml_str2)
        assert nodes4
        # since email is the only child of nodes, we should be able to iterate the parent
        nodes5 = [n for n in nodes4]
        assert len(nodes5) == 1
        assert nodes5[0].subject == 'Goalswarm Node Invite'
        # or the kid
        nodes6 = [n for n in nodes4.email]
        assert len(nodes6) == 1
        assert nodes6[0].subject == 'Goalswarm Node Invite'
        # or using slicing
        node7 = nodes4.email[0]
        assert str(node7.__class__) == 'demisaucepy.xmlnode.XMLNode'
        assert node7.subject == 'Goalswarm Node Invite'
        
    def test_xmlnode_content(self):
        """
        Test the xml nodes List Capabilities
        """
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
        
    def test_poll(self):
        """testing xml of poll"""
        xml_poll = '''
            <poll id="1">
                <name>test poll</name>
                <created>2008-06-30 23:14:45.115906</created>
                <allow_anonymous>False</allow_anonymous>
                <questions>
                    <question id="1" type="radiowtext">
                        <question>why is chocolate good?</question>
                        <options>
                            <option id="1" type="radio">
                                <option>because its sweet!</option>
                            </option>
                            <option id="2" type="radio">
                                <option>because its bitter!</option>
                            </option>
                            <option id="3" type="text">
                                <option>Other</option>
                            </option>
                        </options>
                    </question>
                </questions> 
            </poll>'''
        poll = XMLNode(xml_poll)
        assert poll
        assert poll.id == "1"
        assert poll.name == 'test poll'

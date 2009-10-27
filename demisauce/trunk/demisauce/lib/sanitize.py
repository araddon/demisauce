#!/usr/bin/env python

"""Sanitize.py -- Support functions for web related applications

by Preston Landers <planders@mail.utexas.edu>
Copyleft 1999.  Distributed under the GNU General Public License
Version 0.2  ---  July 20th, 1999

Description:

 Provides several functions to aid in 'sanitizing' user-provided input
 to CGI scripts.  Strips disallowed HTML, HTML'izes plain text, and
 'prettifies' URL's.

See each function comment for usage.

Functions generally useful to the outside world:

 Sanitize(HTML_String):
  Removes all disallowed HTML tags from a string.  Also runs Pretty_Link
  on any embedded links.

 PlainText_to_HTML(Text_string):
  Converts plaintext to something suitable to display in an HTML document.

 Pretty_Link(Link_string):
  Spiffies up a URL according to a variety of rules.
  For example, www.site.com becomes http://www.site.com"""

import re, sys, string

# This regular expression contains a list of HTML that is
# considered valid and allowed.  Anything else is disallowed.

AllowedHTML = re.compile(r"""
    (?isx)              # case-insensitive, multiline, verbose regexp
    </?B> |             # bold
    </?I> |             # italics
    </?P.*?> |          # paragraph (alignment)
    <A .+?> |           # anchors (links)
    </A> |              # anchor close
    </?OL> |            # ordered lists (numbered)
    </?UL> |            # unordered lists (bulleted)
    <LI> |              # list elements
    </?EM> |            # emphasis
    <BR> |              # link breaks
    <HR> |              # horizontal rules
    </?TT> |            # teletype font
    </?STRONG> |        # strong emphasis
    </?BLOCKQUOTE.*?> | # block quotes
    </?ADDRESS> |       # addresses
    </?H[1-6]>          # heading markers
    """)


def HTMLChecker(match_obj):
    """HTMLChecker(match_obj) -- Used by the Sanitize function to validate HTML.

Given an re module match object as a parameter, it will return either
the HTML tag in question if it's allowed, otherwise a null string."""
    
    if AllowedHTML.search(match_obj.group()):
        return match_obj.group()
    else:
        return ""

def LinkChecker(match_obj):
    """LinkChecker(match_obj) - Used by the Sanitize function to validate links.
    
    Given an re module match object as a parameter containing link tag, it
    will return a link tag with the actual link URL validated through
    Pretty_Link() using the normal 'lenient' methods.
    """
    
    return match_obj.group(1) + Pretty_Link(match_obj.group(2)) + match_obj.group(3)


def Sanitize(Content):    # for your protection
    """Sanitize(Content) - Sanitizes HTML strings for your protection.

Given a string containing HTML, it will return that same string with
any disallowed tags removed. (Disallowed tags are those not explicitly
allowed in the regular expression AllowedHTML defined above.)

Also runs any <A HREF=\"link\"> links through Pretty_Link.

TODO: not sure if I should re.escape() the string here or not... If I
do, it would be for the database...?"""
    
    ### strip any illegal HTML
    Content = re.sub(r"(?is)<.+?>", HTMLChecker, Content)

    ### validate any links
    Content = re.sub(r'(?is)(<A .*?HREF=")(.+?)(".*?>)', LinkChecker, Content)
        
    ### then escape any funky characters
    ### TODO: is this really neccesary for the database?
    
    # Content = re.escape(Content)

    return Content

def PlainText_to_HTML(Text):
    """PlainText_to_HTML(Text) - Converts a plain text string to equivelent HTML for display.

This function converts a plain text string to suitable HTML.  In
general, this just means adding <P>'s and <BR>'s.  Also, convert any <
to &lt; so they won't be interpreted as HTML tags."""
    
    Text = string.replace(Text, "<", "&lt;")    
    Text = string.replace(Text, "\n\n", "<P>")
    Text = string.replace(Text, "\n", "<BR>")
    return Text

# this defines valid URL network interfaces for Pretty_Link
NetworkInterfaces = [
    "http",
    "ftp",
    "mailto",
    "gopher",
    "file"
    ]

def Pretty_Link(link, Strict = None):
    """Pretty_Link(link, Strict = None) - Parses URL fragments into more generally useful, valid forms.

This function helps parse user-given link (fragments) into valid URL's

potential link to be parsed is first parameter

second, optional, parameter, if not None, sets 'Strict' parsing which
will return None for a variety of malformed or weird links

the prettified link is returned

Note: most people will NOT want Strict because it can be a real
bastard.  'Lenient' mode makes a real good faith effort to clean up a
URL and shouldn't return a None; in the worst case it will return
'http://some_invalid_url'

Some example cases:
   www.some-site.com  -->   http://www.some-site.com
   ftp://site.com     -->   ftp://site.com  (same)
   not_a_valid_link   -->   None if Strict, otherwise http://not_a_valid_link
   fake://site.com    -->   None if Strict, otherwise http://site.com
   mailto bob@slack.com --> None if Strict, otherwise mailto:bob@slack.com"""

    # strings = re.split(r"([^\-a-zA-Z0-9_]+)",link)[:-1]
    strings = re.split(r"([^\-a-zA-Z0-9_]+)",link)

    if not strings:
        return None
    
    if strings[0] in NetworkInterfaces:
        if strings[1] == "://":
            if Strict:                
                if "." in strings[2:]:
                    return link  # it's valid!
            else:
                return link
        elif strings[0] == "file":
            if strings[1] == ":/":
                return link
            elif strings[1] == ".":
                return "http://" + string.join(strings,"")
            else:
                return None
        elif strings[0] == "mailto":
            if strings[1] == ":":
                if Strict:
                    if "@" in strings[2:] and "." in strings[2:]:
                        return link
                    else:
                        return None
                else:
                    return link
            else:
                if Strict:
                    return None
                else:
                    return "mailto:" + string.join(strings[2:],"")
        else:
            if Strict:
                return None
            else:
                return strings[0] + "://" + string.join(strings[2:],"")
    else:
        # in this case, it's probably just a plain link
        # in the form somesite.com
        # and we'll assume they mean http link
        if Strict:
            if not "." in strings[1:]:
                return None  # handles "nosuchlink" type cases

        if len(strings) > 2 and strings[1] != ".":
            if Strict:
                return None  # handles fake://something
            else:
                return "http://" + string.join(strings,"")
            
        return "http://" + link
    

##
## Some validation code follows; it can be safely ignored
## 

if __name__ == "__main__":
    
    print "You do know this is a module and should not be run directly, right?"

    # print Sanitize(sys.stdin.read())
    # print PlainText_to_HTML(sys.stdin.read())
    
    for line in sys.stdin.readlines():
        link = Pretty_Link(line, "strict")
        if link:
            print "ST: " + line[:-1] + " becomes " + link        
        else:
            print "ST: " + line[:-1] + " becomes None."

        link = Pretty_Link(line)
        if link:
            print line[:-1] + " becomes " + link        
        else:
            print line[:-1] + " becomes None."
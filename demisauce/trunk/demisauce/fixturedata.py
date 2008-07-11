"""
Just a file to store some hard coded data for dumping into DB
"""


cmsitems = [{'title':'Home','content':'''about this day
    this is more stuff''','url':'index.aspx'},
{'title':'Blog','content':'''more content''','url':'blog.aspx','item_type':"folder",'children':[
    {'title':'Announcing Demisauce Version 0.10','content':'''Demisauce Version 0.1 is
    a release that starts to offer full capability to serve content to other applications.
    
    <b>Email Templates</b>, <b>Content</b> are the initial targets.  This release includes the API key security
    C#/Dotnet and Python libraries to integrate with Demisauce Server.
    ''','url':'blog.aspx'},
    {'title':'A Word About The Design','content':'''The Finding Peace design was built on a Windows machine with valid CSS and XHTML 1.0 Strict. It was tested in Windows for FF 2.0, IE 6.0 and with Mac OS X for Safari 1.3.

    It's relased under the Creative Commons License so do what you want with it. The design is from
    <a href="http://design.raykonline.com/templates/peace/index.html"> here</a>.
    ''','url':'blog.aspx'},
]},
{'title':'Features','content':'''more content''','url':'features.aspx','children':[
    {'title':'Content Management','content_type':'html','content':'''<p>The content management is focused on simple web based admin tools
    to edit and organize content.   Most content management systems spend much effort on templating, page layout, 
    hosting, caching, extensions, etc.  Since Demisauce is not a Content Management System in the normal sense
    because it only supplies content not templating or hosting services.
    </p><p>
    The main means of using the Demisauce content are through the Libraries that you would use from your 
    server/application.  Your caching, page layouts etc.
    </p>
    ''','url':'blog.aspx'},
    {'title':'Email Templates','content_type':'rst','content':'''Email templates often ended up embedded in code,
    in configuration files, or an app builds their own db etc.  
    
    Demisauce provides administration tools to edit templates, and web services to retrieve them so your application
    can focus on sending the email, which can still have easy admin tools to change it if need be.
    ''','url':'blog.aspx'},
]},
{'title':'Simple CMS','content':'''more content''','url':'simple.aspx'},
]


site_emails = [
{'subject':'Welcome To Demisauce',
    'key':'welcome_to_demisauce',
    'reply_to':'noreply@yoursite.com',
    'from_email':'youremail@yoursite.com',
    'from_name':'Email From',
    'template': """Welcome to Demisauce, Your account has been enabled, and you can start using services on demisauce.

To verify your account you need to click and finish registering $link

Thank You

Demisauce Team"""},
{'subject':'Invitation to Demisauce',
    'key':'invitation_to_demisauce',
    'reply_to':'noreply@yoursite.com',
    'from_email':'guest@demisauce.org',
    'from_name':'Demisauce Web',
    'template': """Welcome to Demisauce, You have recieved an invite from $from , and an account has been created for you.

To verify your account you need to click and finish registering $link

Thank You

Demisauce Team"""},
{'subject':'Comment Notification',
    'key':'comment-notification',
    'from_email':'guest@demisauce.org',
    'from_name':'Demisauce Web',
    'template': """Hello;

$email has Commented on your $sitename   on page $url

Thank You

Demisauce Team"""},
]


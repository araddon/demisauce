site = '''
[
        {
            "name": "demisauce", 
            "key": "a95c21ee8e64cb5ff585b5f9b761b39d7cb9a202", 
            "email": "sysadmin@demisauce.org", 
            "base_url": "http://localhost:4950",
            "slug": "demisauce",
            "enabled":"True"
        },
        {
            "name": "Django Demo App", 
            "key": "173726158347a26b3836d1c6c09e6c646461517a", 
            "email": "djangodemo@demisauce.org", 
            "slug": "djangodemo",
            "base_url": "http://djangodemo.test:8001",
            "enabled":"True"
        },
        {
            "name": "PHP Demo App", 
            "key": "4cf01693843baaedaf59caf26437cb4b2f0560c6", 
            "email": "phpdemo@demisauce.org", 
            "slug": "phpdemo",
            "base_url": "http://demisauce.test",
            "enabled":"True"
        },
        {
            "name": "your test app", 
            "key": "252484057901f25c1536d1c6c09e6c646461528e", 
            "email": "email@yourdomain.org", 
            "slug": "yoursitename",
            "base_url": "http://demisauce.yoursite.com",
            "enabled":"True"
        },
        {
            "name": "Demisauce Sandbox", 
            "key": "3c5121ce937a1126817b2af30b6604da6a95ffe4", 
            "email": "sandbox@demisauce.org", 
            "slug": "sandbox",
            "base_url": "http://sandbox.demisauce.com",
            "enabled":"True",
            "description":"This is a sandbox for testing your app without touching production data"
        },
        {
            "name": "Local Food", 
            "key": "aaabbbcccddd1126817b2af30b6604da6a95ffe4", 
            "email": "araddon+localfood@gmail.com", 
            "slug": "localfood",
            "base_url": "http://api.towngrub.com",
            "enabled":"True",
            "description":"This is a dev for towngrub"
        }
]'''
person = '''
[
        {
            "site_id": "1", 
            "displayname": "Sys Admin @Demisauce", 
            "email": "sysadmin@demisauce.org", 
            "raw_password": "admin",
            "isadmin": "True",
            "verified": "True",
            "waitinglist": "False",
            "issysadmin": "True"
        },    
        {
            "site_id": "1", 
            "displayname": "Admin @Demisauce", 
            "email": "admin@demisauce.org", 
            "raw_password": "admin",
            "isadmin": "True",
            "verified": "True",
            "waitinglist": "False",
            "issysadmin": "False"
        },    
        {
            "site_id": "2", 
            "displayname": "Djangodemo admin", 
            "email": "djangodemo@demisauce.org", 
            "raw_password": "admin",
            "isadmin": "True",
            "verified": "True",
            "waitinglist": "False",
            "issysadmin": "False"
        },    
        {
            "site_id": "3", 
            "displayname": "phpdemo admin", 
            "email": "phpdemo@demisauce.org", 
            "raw_password": "admin",
            "isadmin": "True",
            "verified": "True",
            "waitinglist": "False",
            "issysadmin": "False"
        }
]'''
app = '''
[
        {
            "site_id": "1",
            "owner_id": "1",
            "name": "demisauce.com", 
            "list_public" : "1",
            "slug": "demisauce",
            "base_url": "http://localhost:4950", 
            "authn": "demisauce"
        },{
            "site_id": "1",
            "owner_id": "1",
            "name": "demisauce.com alternate api", 
            "slug": "demisaucealt",
            "base_url": "http://localhost:4950", 
            "authn": "demisauce"
        },{
            "site_id": "2",
            "owner_id": "3",
            "name": "djangodemo", 
            "slug": "djangodemo",
            "base_url": "http://djangodemo.test:8001", 
            "authn": "none"
        },{
            "site_id": "3",
            "owner_id": "4",
            "name": "phpdemo", 
            "slug": "phpdemo",
            "base_url": "http://demisauce.test", 
            "authn": "none"
        },{
            "site_id": "1",
            "owner_id": "1",
            "name": "wordpress", 
            "slug": "wordpress",
            "base_url": "http://192.168.0.106/blog/xmlrpc.php", 
            "authn": "xmlrpc"
        },{
            "site_id": "1",
            "owner_id": "1",
            "name": "delicious.com", 
            "slug": "deliciouscom",
            "base_url": "http://delicious.com", 
            "authn": "none"
        },{
            "site_id": "1",
            "owner_id": "1",
            "name": "delicious feeds", 
            "slug": "deliciousfeeds",
            "base_url": "http://feeds.delicious.com", 
            "authn": "none"
        }
]'''

service = '''
[
        {
            "site_id": "1",
            "app_id": "1",
            "owner_id": "1",
            "list_public": "1",
            "name": "Poll Html Service", 
            "method_url": "/api/poll/{key}.{format}?apikey={api_key}", 
            "key": "poll",
            "views": "",
            "description": "Simple Polls, embeddable within your application"
        },{
            "site_id": "1",
            "app_id": "1",
            "owner_id": "1",
            "list_public": "1",
            "name": "Comment Html Service", 
            "method_url": "/api/comment/{key}.{format}?apikey={api_key}", 
            "key": "comment",
            "views": "",
            "description": "Comment html and form "
        },{
            "site_id": "1",
            "app_id": "1",
            "owner_id": "1",
            "list_public": "1",
            "name": "Email Template Sending service", 
            "method_url": "/api/email/{key}.{format}?apikey={api_key}", 
            "key": "email",
            "format": "xml",
            "description": "Email template, Get, Post"
        },{
            "site_id": "2",
            "app_id": "3",
            "owner_id": "3",
            "name": "django secure hello world html service", 
            "method_url": "service/helloworld/", 
            "key": "helloworld",
            "views": "",
            "description": "hello world test service "
        },{
            "site_id": "3",
            "app_id": "4",
            "owner_id": "4",
            "name": "Php Demo secure hello world html service", 
            "method_url": "service/helloworld/", 
            "key": "helloworld",
            "views": "",
            "description": "secure hello world"
        },{
            "site_id": "1",
            "app_id": "1",
            "owner_id": "1",
            "list_public": "1",
            "name": "Help/Idea/Feedback Submission widget.", 
            "method_url": "help/feedback_service/{request}", 
            "key": "feedback",
            "views": "badge,publiclist,adminrecent,adminfiltered",
            "description": "An Idea, Problem, Feedback set of services."
        },{
            "site_id": "1",
            "app_id": "6",
            "owner_id": "1",
            "list_public": "1",
            "name": "Delicious Tags Html Page", 
            "method_url": "/tag/{key}", 
            "key": "tag",
            "views": "",
            "description": "Just gets a page on delicious"
        },{
            "site_id": "1",
            "app_id": "5",
            "owner_id": "1",
            "name": "Wordpress content service", 
            "method_url": "metaWeblog.getRecentPosts", 
            "key": "wordpress",
            "format": "xmlrpc",
            "views": "",
            "description": "Wordpress CMS extraction service"
        }
]'''

email = '''
[
        {
            "site_id": "1", 
            "subject":"Welcome To Demisauce",
            "key":"welcome_to_demisauce",
            "from_email":"guest@demisauce.org",
            "from_name":"Demisauce Admin",
            "template": "Welcome to Demisauce;\
\\n\\nYour account has been enabled, and you can start using services on demisauce.\
\\n\\nTo verify your account you need to click and finish registering $link\
\\n\\nThank You\\n\\nDemisauce Team"
        },    
        {
            "site_id": "1", 
            "subject":"Invitation to Demisauce",
            "key":"invitation_to_demisauce",
            "from_email":"guest@demisauce.org",
            "from_name":"Demisauce Web",
            "template": "Welcome to Demisauce;\
\\n\\nYou have recieved an invite from $from , and an account has been created for you.\
\\n\\nTo verify your account you need to click and finish registering $link\
\\n\\nThank You\\n\\nDemisauce Team"
        },    
        {
            "site_id": "1", 
            "subject":"Thank You for registering with Demisauce",
            "key":"thank_you_for_registering_with_demisauce",
            "from_email":"guest@demisauce.org",
            "from_name":"Demisauce Web",
            "template": "Welcome to Demisauce;\
\\n\\nWe are are currently allowing a few users to try out our hosted service, and will send you an invite \
when we can accept more testers.  However, this is also an open source project so please feel free to download \
and try it out yourself.\
\\n\\nMore info at http://www.demisauce.com\
\\n\\nYour Email address $email will not be used other than for logging in.\
\\n\\nThank You\\n\\nDemisauce Team"
        },    
        {
            "site_id": "1", 
            "subject":"A new user has registered",
            "key":"a-new-user-has-registered",
            "from_email":"guest@demisauce.org",
            "from_name":"Demisauce Admin",
            "template": "A new user has signed up at demisauce.\
\\nTheir Email address $email and $displayname\
\\n\\nThank You\\n\\nThe Demisauce Team"
        },   
        {
            "site_id": "1", 
            "subject":"Comment Notification",
            "key":"comment-notification",
            "from_email":"guest@demisauce.org",
            "from_name":"Demisauce Web",
            "template": "Hello;\
\\n\\n$email has Commented on your $sitename on page $url\
\\n\\nThank You\\n\\nDemisauce Team"
        }
]'''





site = '''
{
    "class": "demisauce.model.site.Site", 
    "data": [
        {
            "name": "demisauce.com", 
            "key": "a95c21ee8e64cb5ff585b5f9b761b39d7cb9a202", 
            "email": "sysadmin@demisauce.org", 
            "slug": "demisauce.com",
            "enabled":"True"
        },    
        {
            "name": "Django Demo App", 
            "key": "173726158347a26b3836d1c6c09e6c646461517a", 
            "email": "djangodemo@demisauce.org", 
            "slug": "djangodemo",
            "base_url": "http://localhost:4951",
            "enabled":"True"
        },    
        {
            "name": "your test app", 
            "key": "252484057901f25c1536d1c6c09e6c646461528e", 
            "email": "email@yourdomain.org", 
            "slug": "yourdemisauce.slug",
            "base_url": "http://demisauce.yoursite.com",
            "enabled":"True"
        }]
}'''
service = '''
{
    "class": "demisauce.model.service.Service", 
    "data": [
        {
            "site_id": "1",
            "name": "demisauce.com", 
            "key": "a95c21ee8e64cb5ff585b5f9b761b39d7cb9a202", 
            "email": "sysadmin@demisauce.org", 
            "slug": "demisauce.com",
            "enabled":"True"
        }]
}'''
person = '''
{
    "class": "demisauce.model.person.Person", 
    "data": [
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
        }]
}'''

email = '''
{
    "class": "demisauce.model.email.Email", 
    "data": [
        {
            "site_id": "1", 
            "subject":"Welcome To Demisauce",
            "key":"welcome_to_demisauce",
            "from_email":"guest@demisauce.org",
            "from_name":"Demisauce Admin",
            "template": "Welcome to Demisauce, Your account has been enabled, and you can start using services on demisauce.

            To verify your account you need to click and finish registering $link

            Thank You

            Demisauce Team"
        },    
        {
            "site_id": "1", 
            "subject":"Invitation to Demisauce",
            "key":"invitation_to_demisauce",
            "from_email":"guest@demisauce.org",
            "from_name":"Demisauce Web",
            "template": "Welcome to Demisauce, You have recieved an invite from $from , and an account has been created for you.

To verify your account you need to click and finish registering $link

Thank You

Demisauce Team"
        },    
        {
            "site_id": "1", 
            "subject":"Thank You for registering with Demisauce",
            "key":"thank_you_for_registering_with_demisauce",
            "from_email":"guest@demisauce.org",
            "from_name":"Demisauce Web",
            "template": "Welcome to Demisauce, we are are currently allowing a few users to try out our hosted service, and will send you an invite when we can accept more testers.  However, this is also an open source project so please feel free to download and try it out yourself.  

More info at http://www.demisauce.org 
or at:   http://demisauce.googlecode.com

Your Email address $email will not be used other than for logging in.

Thank You

The Demisauce Team"
        },    
        {
            "site_id": "1", 
            "subject":"Comment Notification",
            "key":"comment-notification",
            "from_email":"guest@demisauce.org",
            "from_name":"Demisauce Web",
            "template": "Hello;

$email has Commented on your $sitename   on page $url

Thank You

Demisauce Team"
        }]
}'''

comment = '''
{
    "class": "demisauce.model.comment.Comment", 
    "data": [
        {
            "site_id": "1", 
            "person_id": "1", 
            "comment": "test comment", 
            "uri": "/url/where/person/commented",
            "isuser":"True",
            "hashedemail":"0c0342d8eb446cd7743c3f750ea3174f",
            "email":"sysadmin@demisauce.org",
            "authorname":"Sysadmin @ Demisauce"
        }]
}'''

poll = '''
{
    "class": "demisauce.model.poll.Poll", 
    "data": [
        {
            "site_id": "1", 
            "person_id": "1", 
            "name": "What should the new features be?", 
            "key":"what-should-the-new-features-be",
            "response_count": "0"
        }]
}'''
poll_question = '''
{
    "class": "demisauce.model.poll.Question", 
    "data": [
        {
            "poll_id": "1", 
            "question": "What should the new features be?", 
            "type":"radiowother",
            "response_count": "0"
        }]
}'''

poll_question_option = '''
{
    "class": "demisauce.model.poll.QuestionOption", 
    "data": [
        {
            "question_id": "1", 
            "sort_order": "1", 
            "option": "security", 
            "type":"radio"
        }]
}'''




:tocdepth: 4

.. _api:

================================================
Demisauce API Info
================================================

The api is a set of services to get access to data, and also used to call settings to define what plugins to use.  These are restful services that implement GET/POST/PUT/DELETE operations.

General Workflow
---------------------------
Generally you will be doing calling an api to add or get data.   If you are adding data to demisauce (say adding a new user) then each object type has a set of events *new_user* *update_user* which you plugins can subscribe to.   This is how the integrations with apps are implemented.

Services Available
---------------------------
- **user**          Add/Update user, get info, has key/value attribute's
- **group**         Create groups, add users to groups.  (useful for email lists,other apps)


User
-------------
.. new_user::

    upon new user

.. update_user::

   updating user


Example
------------------------

Python example ::
    
    person_data = {
        'email':'email@email.com',
        'displayname':'library testing user',
        'url':'http://testingurls.com',
        'authn':'local',
        'foreign_id': 515,
        'attributes':[{'name':'FollowNotification','value':'all','category':'notification'}],
        'extra_json':{
            'your_info':'value1',
            'age':99
        }
    }
    user = DSUser(person_data)
    user.POST()



Response Codes
---------------------------
- 200           **ok**: Request was successful and response body has the
                json/xml requested.
- 201           **Created**: Service requests that create or update an item, 
                response contains representation of object updated
- 204           **No Content**:  Request was successful but no response is
                avaialable (deleted?)

- 400           **Bad Request**:  request was bad in some unspecified way

- 404           **Not Found**:  The requested service/object not found




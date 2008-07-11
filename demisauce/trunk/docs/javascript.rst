Demisauce Javascript Library doc
================================================

.. _demisauce_javascript:

This Section is about the Javascript api's based on `jquery <http://jquery.com>`_, which is
used extensively in Demisauce.  


=======================================
Embed Demisauce in your app: ds.base.js
=======================================

ParseURI
--------------
This is a the fantastic `parseUri <http://stevenlevithan.com/demo/parseuri/js/>`_ library
which we have included and then modified only to fit in as a plugin in non-global namespace.

.. code-block:: javascript
    
    var result = $.ds.parseUri(window.location.href);
    if (opts.use_url == true){
        if (opts.absolute == true) {
            opts.activity = result.protocol + '://' + result.authority;
        }
        opts.activity += result.relative;
    }
    url += '&activity=' + encodeURIComponent(opts.activity);
    

Help System JS
--------------
Use's our modifed Facebox jquery plugin.  It does a facebox popup (maybe dift later)
for the comments, help(feedback), and help content, as well as group admin.


Comment System JS
-----------------

tbd


Activities
----------

Activity plugin, allow links, forms, etc to have their
events observed and acted upon.  The ideas is to be able to 
track activities for a specific person (instead of broad population tracking)
such as `Google Analytics <http://www.google.com/analytics/>`_.  Also
you can use it when a page loads


example markup:

.. code-block:: javascript
    
    <a href="#" class="ds_activity" activity="this is the activity">activity2</a>
    
    <script>
        jQuery(document).ready(function() {
            $('a.ds_activity').dsactivity();
        });
    </script>

Example Markup for a page loading (After a user log's on)

.. code-block:: javascript
    
    <script>
        
        $.ds.dsactivity({activity:"User logged on",category:"Account"});
        
    </script>


*$.ds.dsactivity()*:  Static method to add tracking record for an activity

::
    
    jQuery('#your_activity').click(function() {
        $.ds.humanMsg.displayMsg('You Just Performed the Test Activity');
    });
    


*OPTIONS*

:use_url:   the current url (relative by default) will be used as the 
            text identifier for the activity

:absolute:  the absolute (fully qualified url) will be used not relative url

:activity:  the text string to track as the "Activity" 

:unique_id: this is an optional argument you can use to pass your unique identifier
            such as an integer/guid etc to allow for filtering.  example:  Activity 
            might be "purchase", @unique_id might be "146" for a product id


Hints
-------------
Hints are aid's to user's that are embedded in form fields, when you enter the cursor
the hints are removed.  They are also removed before submittal.

.. raw:: html

   <a href="http://www.flickr.com/photos/53228015@N00/2639983271/" title="Demisauce Hints Flickr">
    <img src="http://farm4.static.flickr.com/3269/2639983271_ff37243b0b_o.png"  alt="Hints" border="0" />
   </a>


::
    
    <form id="commentform">
        <input type="text" name="email" id="email" value='Please Enter your Email'  class="hint" size="22" tabindex="2" />
        <input type="submit" value="submit" />
    </form>
    <script type="text/javascript">
        $(document).ready(function(){
            $('#commentform').dshints();
        });
    </script>
    
================
ds.slugeditor.js
================
The slug editor allows RESTful url's to be created from names, titles, etc.  We will
use these extensively for URL's instead of ID's

For example, this shows the html mark up (without api key) to get xml for an email template.

.. code-block:: html

    <a href="http://demisauce.com/api/xml/email/thank_you_for_registering_with_demisauce">Link To View Xml</a>

.. raw:: html

    <a href="http://www.flickr.com/photos/53228015@N00/2640013293/" title="Slug Editor showing pre-edit">
        <img src="http://farm4.static.flickr.com/3034/2640013293_f8d9341da0_o.png"  border="0"  /></a>
    <br /><br />
    Showing the Slug Editor being edited.
    <br />
    <a href="http://www.flickr.com/photos/53228015@N00/2640013313/" title="Slug Editor showing Edit mode">
        <img src="http://farm4.static.flickr.com/3049/2640013313_5d9f448811_o.png" border="0"  /></a>
        
        
Usage
------

Demisauce Slug Editor Depends on JQuery


.. code-block:: html
    
    <div class="required">
        <label for="subject">Subject:</label>
        <input type="Text" name="subject" value="" id="subject"/>
    </div>
    <div class="required" id="permalink_div">
        <label for="slug">Permalink:</label>
        <span id="permalink" class="secondary">
            <span id="editable-slug-span" title="Click to edit this part of the permalink">editable slug</span>
            <a href="javascript:void(0)" id="editable-slug-href">Edit</a>
        </span>
        <input type="hidden"  size="100" id="permalink"  value="$yourcode" /><br />
        <input type="text" size="100" id="real_permalink" name="real_permalink" 
                value="$yourcode" style="display:none;"/>
    </div>
    <script type="text/javascript">
    $(document).ready(function(){
        $('#emailform').slugeditor({slugfrom: '#subject'});
    });
    </script>    
    
*OPTIONS*:
    
    :permalink_sel:   the jquery selector pattern for the textbox of the slug/permalink to edit
                   Default:   "#real_permalink"
    
    :permalink_span:  jquery selector pattern for the span displaying the slug
                    in non form textbox, which you can click on to edit
                    Default: = '#editable-slug-span'
    
    :permalink_edit:  jquery selector pattern for the link to "edit" the slug 
                    Default: = '#editable-slug-href'
    
    :slugfrom:      the form field to get the initial slug from (for conversion)
                    Default: = '#title'




================
Facebox
================

This uses the `facebox jquery plugin <http://famspam.com/facebox/>`_ but has been fairly
extensively modifed for suitability here.   

Changes are mostly to allow for cross-domain javascript support through other methods
of getting content other than the ajax and remote html methods in the original facebox.


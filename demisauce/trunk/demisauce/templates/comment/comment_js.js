if (typeof DEMISAUCE == "undefined") {
    /**
     * The Demisauce NameSpace
    */
    var DEMISAUCE = {};
}
(function(){
/* Demisauce Core Javascript
 *
 * $Date: 2008-5-16
  Demisauce Comments Script:  Load in jquery, and 
     jquery plugin (dsemisauce.js) to handle interaction
     with demisauce server.  

     this script is used to parse the Container/Host page's url, in order
     to use it for return purposes on redirect (after logon)
     
     OPTIONS:
     
        @comment_id:    the id of Div or content placeholder to inject the 
                        comment system html
                        Default:   "demisauce-comments"
                        
        @site_slug:     the name of the site you provided when you signed up 
                        on demisauce server (go to Account -> Siteinfo)
        
        @base_url:      the url of demisauce server:  defaults to http://localhost:4950 
        
        @url:           the uniqueid of this collection of comments.  This defaults to the current page url.
                        ie:   http://yourblog.com/entry/your-article-about-stuff
                        you can override to anything, does not have to be a full url, just uniquie:
                        ie:   /products/123456


    //SAMPLE MARKUP
    
    <div id="demisauce-comments"></div>
    <script type="text/javascript" src="http://www.demisauce.org/comment/js/yoursitename.js"></script>
    <script type="text/javascript">
        window.onload = function () {
            DEMISAUCE.comment.init({
                site_slug: 'yoursitename',
                base_url: 'http://www.demisauce.org', 
            });
        };
    </script>
    
    OR
    
    <div id="demisauce-comments"></div>
    <script type="text/javascript" src="http://www.demisauce.org/comment/js/yoursitename.js"></script>
    <script type="text/javascript">
        window.onload = function () {
            DEMISAUCE.comment.init({
                site_slug: 'yoursitename',
                base_url: 'http://www.demisauce.org', 
                url: '/myurl/productid/12345'  //override current url, only has to be unique, not a "url"
            });
        };
    </script>
    
 */



    /**
     * comment initiator js
     * @class DEMISAUCE.comment
    */
    
    DEMISAUCE.comment = {

        init: function(options) {
            var defaults = {
                comment_id: 'demisauce-comments',
                base_url: '',
                url: '',
                site_slug: '',
                jquery_noconflict: false
            };
            // Extend our default options with those provided.
            for ( var i in defaults ) {
                if (i in options) defaults[i] = options[i];
            }
            var opts = defaults;
            
            
            var demisauce_basediv = document.createElement('div');
            demisauce_basediv.id = 'demisauce-comments-content';
            document.getElementById(opts.comment_id).parentNode.appendChild(demisauce_basediv);
            
            var ds_link = window.location.href;
            
            var qs = 'site_slug=' + opts.site_slug;
            qs += '&userhash=${c.hash}';
            qs += '&url=' + encodeURIComponent(ds_link);
            qs += '&urlbypass=' + encodeURIComponent(opts.url);
            
            // this requires jquery, so lets go ahead and use it if they haven't
            if ( typeof jQuery == "undefined" ) {
                var ds_jquery_script = document.createElement('script');
                ds_jquery_script.type = 'text/javascript';
                ds_jquery_script.src = opts.base_url + '/js/jquery-1.2.6.min.js'
                demisauce_basediv.appendChild(ds_jquery_script);
            }
            
            var ds_comments_script = document.createElement('script');
            ds_comments_script.type = 'text/javascript';
            ds_comments_script.src = opts.base_url + '/js/ds.base.js'
            
            var ds_comments_content = document.createElement('script');
            ds_comments_content.type = 'text/javascript';
            ds_comments_content.src = opts.base_url + '/comment/js2/' + opts.site_slug + '?' +  qs
            //alert(ds_comments_content.src)
            
            // now load the two scripts
            demisauce_basediv.appendChild(ds_comments_script);
            demisauce_basediv.appendChild(ds_comments_content);
            
            var content_div = document.createElement('div');
            content_div.id = 'demisauce_comment_form_div'
            demisauce_basediv.appendChild(content_div);
            
            
        },

        refresh: function() {
            //???
        }
    };
    
    //DEMISAUCE.comment.init();
   
})();
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
                        
        @site_key:      the key provided when you signed up on demisauce server (go to settings)
        
        @base_url:      the url of demisauce server:  defaults to http://localhost:4950 
        
        @url:           the uniqueid of this collection of comments.  This defaults to the current page url.
                        ie:   http://yourblog.com/entry/your-article-about-stuff
                        you can override to anything, does not have to be a full url, just uniquie:
                        ie:   /products/123456


    //SAMPLE MARKUP
    
    <div id="demisauce-comments"></div>
    <script type="text/javascript" src="http://www.demisauce.org/js/demisauce.js"></script>
    <script type="text/javascript">
        function demisauce_init() {
            DEMISAUCE.comment.init({
                site_key: '8c729abd0944981fe12372901a1aca378b053a0a',
                base_url: 'http://www.demisauce.org', 
            })
        }
        window.onload=demisauce_init;
    </script>
    
    OR
    
    <div id="demisauce-comments"></div>
    <script type="text/javascript" src="http://www.demisauce.org/js/demisauce.js"></script>
    <script type="text/javascript">
        function demisauce_init() {
            DEMISAUCE.comment.init({
                site_key: '8c729abd0944981fe12372901a1aca378b053a0a',
                base_url: 'http://www.demisauce.org', 
                url: '/myurl/productid/12345'  //override current url, unly has to be unique, not a "url"
            })
        }
        window.onload=demisauce_init;
    </script>
    
 */



    /**
     * comment initiator js
     * @class DEMISAUCE.comment
    */
    /*
    DEMISAUCE.comment = {

        init: function(options) {
            var defaults = {
                comment_id: 'demisauce-comments',
                base_url: 'http://localhost:4950',
                url: '', // the uniqueid for these comments, override current url
                site_key: '',
                jquery_noconflict: false
            };
            // Extend our default options with those provided.
            for ( var i in defaults ) {
                if (i in options) defaults[i] = options[i];
            }
            var opts = defaults;
            
            //alert('in init ' + opts.site_key)
            var demisauce_basediv = document.createElement('div');
            demisauce_basediv.id = 'demisauce-comments-content';
            document.getElementById(opts.comment_id).parentNode.appendChild(demisauce_basediv);
            
            var ds_link = window.location.href;
            var qs = 'site_key=' + opts.site_key;
            if (opts.url != '') {
                ds_link = opts.url;
            }
            qs += '&url=' + encodeURIComponent(ds_link);
            ds_link = encodeURIComponent(ds_link);
            
            // this requires jquery, so lets go ahead and use it if they haven't
            if ( typeof jQuery == "undefined" ) {
                var ds_jquery_script = document.createElement('script');
                ds_jquery_script.type = 'text/javascript';
                ds_jquery_script.src = opts.base_url + '/js/jquery-1.2.3.min.js'
                demisauce_basediv.appendChild(ds_jquery_script);
            }
            
            var ds_comments_script = document.createElement('script');
            ds_comments_script.type = 'text/javascript';
            ds_comments_script.src = opts.base_url + '/js/ds.comments.jq.js'
            
            var ds_comments_content = document.createElement('script');
            ds_comments_content.type = 'text/javascript';
            ds_comments_content.src = opts.base_url + '/comment/js2?' +  qs
            
            // now load the two scripts
            demisauce_basediv.appendChild(ds_comments_script);
            demisauce_basediv.appendChild(ds_comments_content);
            
            var content_div = document.createElement('div');
            content_div.id = 'demisauce_comment_form_div'
            demisauce_basediv.appendChild(content_div);
            
            var output = '<div id="ds-commentform-div"><iframe width="100%" height="200" frameborder="0" \
                src="' + opts.base_url + '/comment/commentform?' + qs + '"  allowtransparency="true" \
                vspace="0" hspace="0" marginheight="0" marginwidth="0" name="ds-comment-login"></iframe></div>\
                <div id="ds-logonform-div" style="display:none;"></div> \
                <a href="javascript:void(0);" id="ds-logon-link" >Show Logon</a> \
                <a href="javascript:void(0);" id="ds-showcommentform-link" style="display:none;">Cancel</a> \
                <form><input type="hidden" id="source_url" name="source_url" value="' + ds_link + '" /></form>';
            
            content_div.innerHTML = output;
        },

        refresh: function() {
            //???
        }
    };
    */
    
    //DEMISAUCE.comment.init();
   
})();
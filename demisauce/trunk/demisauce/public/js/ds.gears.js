(function($){
    
    //alert('in ds.gears.js')
    $.ds = $.ds || {};
    
    $.extend($.ds,{
        gears: {},
        debug_selector:'#debug_output',
        message: function(msg) {
            $(this.debug_selector).html(msg);
        }
    })
    
    $.extend($.ds.gears, {
        resource_store_name:'gears_store_name',
        resource_store:null,
        managed_store_name:'demisauce_managed_store',
        managed_store_manifest:'/GearsSamplesAndTools/samples/simple/gears_manifest.json',
        managed_store:null,
        local_server:null,
        loaded:false,
        init: function(options) {
            var opts = {
                debug: false
            };
            options = options || {}; $.extend(opts, options); //Extend and copy options
            if (!window.google || !google.gears) {
                 //location.href = "http://gears.google.com/?action=install&message=Welcome To Demisauce&return=http://localhost:4950";
            } else {
                if (!google.gears.factory.hasPermission){
                    google.gears.factory.getPermission('Demisauce', '/images/info.png', 'Help speed up this site with with Gears!')
                }
                this.local_server = google.gears.factory.create("beta.localserver");
                this.resource_store = this.local_server.openStore(this.resource_store_name);
                //this.managed_store = this.local_server.createManagedStore(this.managed_store_name);
                
                this.loaded = true;
                if (opts.debug) this.init_debug();
                
            }
        },
        init_debug: function () {
            $('body').append('<style type="text/css"> \
                .gears_info{position:absolute;background-color:#134275;bottom:0;left:0;width:100%;height:40px;} \
                div.gears_info p {color: #fff;font-style: italic;font-weight: bold;font-size: large;} \
                div.gears_info span {color: yellow;font-style: italic;font-weight: bold;font-size: large;} \
                body>div#footer{position:fixed;} \
            </style><div class="gears_info"><p>Resource \
            Store Status: <span id="resourceStatus" class="style3"></span></p></div>');
            $.ds.message("Yeay, Gears is already installed.");
            if (!this.resource_store){
                $('#resourceStatus').html('nope, not created');
            } else {
                $('#resourceStatus').html('yup, resource store exists');
            }
        },
        create_store: function(){
            if (!this.loaded) return;
            
            //this.managed_store.manifestUrl = this.managed_store_manifest;
            //this.managed_store.checkForUpdate();
            this.resource_store = this.local_server.createStore(this.resource_store_name);
            var self = this;
            var out_msg = 'now available offline:';
            $('img,script').each(function (){
                self.resource_store.capture(this.src,function (url,success,captureId){
                    out_msg += ', ' + url;
                });
            });
            $('link[rel*=stylesheet]').each(function (){
                self.resource_store.capture(this.href,function (url,success,captureId){
                    out_msg += ', ' + url;
                });
            });
            if (opts.debug) $.ds.message(out_msg);
            
            /*  
            var timerId = window.setInterval(function() {
                // When the currentVersion property has a value, all of the resources
                // listed in the manifest file for that version are captured. There is
                // an open bug to surface this state change as an event.
                if ($.ds.gears.managed_store.currentVersion) {
                    window.clearInterval(timerId);
                    $.ds.message("The documents are now available offline.\n" + 
                            "With your browser offline, load the document at " +
                            "its normal online URL to see the locally stored " +
                                  "version. The version stored is: " + 
                            $.ds.gears.managed_store.currentVersion);
                    } else if ($.ds.gears.managed_store.updateStatus == 3) {
                    $.ds.message("Error: " + $.ds.gears.managed_store.lastErrorMessage);
                }
            }, 500);
            */
        },
        remove_store: function(){
            if (!this.loaded) return;
            if (this.managed_store)
                this.local_server.removeManagedStore(this.managed_store_name);
            this.local_server.removeStore(this.resource_store_name);
            this.loaded = false;
        }
    });
    
})(jQuery);
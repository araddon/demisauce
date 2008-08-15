(function($){
    
    //alert('in ds.gears.js')
    $.ds = $.ds || {};
    
    $.extend($.ds,{
        gears: {},
        debug_selector:'#debug_output',
        message: function(msg) {
            $(this.debug_selector).append(msg);
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
            this.loaded = false;
            this.gears_installed = false;
            this.gears_enabled = false; //for this site
            this.options = options || {}; $.extend(opts, options); //Extend and copy options
            if (!window.google || !google.gears) {
                // not installed
            } else {
                this.gears_installed = true;
                $.ds.message("Yeay, Gears is already installed.");
                if (google.gears.factory.hasPermission){
                    this.load_db();
                    this.gears_enabled = true;
                }
                if (opts.debug) this.init_debug();
            }
        },
        install_gears: function(){
            var url = window.location.href;
            location.href = "http://gears.google.com/?action=install&message=Welcome To Demisauce&return=" + url;
        },
        enable_gears: function(){
            // unser initiated event to install
            if (!google.gears.factory.hasPermission){
                google.gears.factory.getPermission('Demisauce', '/images/info.png', 'Help speed up this site with with Gears!')
                if (google.gears.factory.hasPermission){
                    this.load_db();
                    this.create_store();
                }
            } else {
                this.load_db();
                this.create_store();
            }
        },
        load_db: function(){
            this.local_server = google.gears.factory.create("beta.localserver");
            this.resource_store = this.local_server.openStore(this.resource_store_name);
            //this.managed_store = this.local_server.createManagedStore(this.managed_store_name);
            this.loaded = true;
        },
        init_debug: function () {
            var self = this;
            var out_html = '<style type="text/css"> \
                .gears_info{position:absolute;background-color:#134275;bottom:0;left:0;width:100%;height:60px;} \
                div.gears_info p {color: #fff;font-style: italic;font-weight: bold;font-size: large;} \
                div.gears_info span {color: yellow;font-style: italic;font-weight: bold;font-size: large;} \
                body>div#footer{position:fixed;} \
            </style><div class="gears_info"><span id="debug_output"></span><p>Resource \
            Store Status: <span id="resourceStatus" class="style3"></span>'
            if (!this.loaded) 
                out_html += '<a href="#" id="gears_create_store">Create Store</a>';
            if (!this.gears_installed) 
                out_html += '<a href="#" id="gears_install">Install Gears for Turbo</a>';
            if (!this.gears_enabled) 
                out_html += '<a href="#" id="gears_enable">Turbo!</a>';
            //out_html += '<a href="#" id="gears_whats_instore">Whats In Store?</a>'
            out_html += '</p></div>'
            $('body').append(out_html);
            $('#gears_create_store').click(function(){
                self.create_store();
            });
            $('#gears_install').click(function(){
                self.install_gears();
            });
            $('#gears_enable').click(function(){
                self.enable_gears();
            });
            $('#gears_whats_instore').click(function(){
                //self.create_store();
            });
            
            if (!this.resource_store){
                $('#resourceStatus').html('nope, not created');
            } else {
                $('#resourceStatus').html('yup, resource store exists');
            }
        },
        show_store: function(){
            
        },
        create_store: function(){
            //if (!this.loaded) return;
            
            //this.managed_store.manifestUrl = this.managed_store_manifest;
            //this.managed_store.checkForUpdate();
            this.resource_store = this.local_server.createStore(this.resource_store_name);
            var self = this;
            var out_msg = 'now available offline:';
            //$('img,script')
            var files_to_capture = [];
            $('script[gears=true]').each(function (){
                alert(this.src);
                files_to_capture.push(this.src);
            });
            alert('before capture' + files_to_capture[0])
            self.resource_store.capture(files_to_capture,function (url,success,captureId){
                alert('in capture ' + url + + (success ? 'succeeded' : 'failed'))
                out_msg += ', ' + url;
            });
            //alert(out_msg);
            /*
            $('link[rel*=stylesheet]').each(function (){
                self.resource_store.capture(this.href,function (url,success,captureId){
                    out_msg += ', ' + url;
                });
            });
            */
            if (opts.debug) $.ds.message(out_msg);
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
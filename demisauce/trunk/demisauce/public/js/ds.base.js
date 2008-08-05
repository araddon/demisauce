(function($)
{
    //If the Demisauce scope is not availalable, add it
    $.ds = $.ds || {};
    $.extend($.ds, {
        /*
            parseUri 1.2.1
            (c) 2007 Steven Levithan <stevenlevithan.com>
            http://stevenlevithan.com/demo/parseuri/js/
            MIT License
            
            Demisauce mods:  namespaced it to not pollute global
        */
        parseUri : function (str) {
            var o   =  {
                strictMode: false,
                key: ["source","protocol","authority","userInfo","user","password","host","port","relative","path","directory"
            ,"file","query","anchor"],
                q:   {
                    name:   "queryKey",
                    parser: /(?:^|&)([^&=]*)=?([^&]*)/g
                },
                parser: {
                    strict: /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*):?([^:@]*))?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
                    loose:  /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*):?([^:@]*))?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/
                }
            }
            var m   = o.parser[o.strictMode ? "strict" : "loose"].exec(str),
                uri = {},
                i   = 14;
            while (i--) uri[o.key[i]] = m[i] || "";
            uri[o.q.name] = {};
            uri[o.key[12]].replace(o.q.parser, function ($0, $1, $2) {
                if ($1) uri[o.q.name][$1] = $2;
            });
            return uri;
        },
        /* Shared Services for rest of DemiSauce JS
        */
        defaults : {
            logon_form_loaded: false,
            logon_form_selector: '#ds-logonform-div',
            logon_form_cancel: '#ds-showinputform-link',
            logon_form_link: '#ds-logon-link',
            input_form_selector: '#ds-inputform-div',
            current_url : '',
            base_url: 'http://localhost:4950',
            site_slug: 'enter your site id here' // unique id for usage, set in admin panel
        },
        prepLogon : function(el) {
            $(el).append('<div id="ds-logonform-div" style="display:none;"></div> \
                <a href="javascript:void(0);" id="ds-logon-link" >Show Logon</a> \
                <a href="javascript:void(0);" id="ds-showinputform-link" style="display:none;">Cancel</a>');
            var self = this; var o = this.defaults;
            $(o.logon_form_link).click(function(){
                self.showLogon();
            });
            $(o.logon_form_cancel).click(function(){
                self.hideLogon();
            });
        },
        showLogon: function() {
            var self = this; var o = this.defaults;
            if (o.logon_form_loaded == true) {
                
            }else{
                o.logon_form_loaded = true;
                var qs = 'url=' + encodeURIComponent(o.current_url);
                $(o.logon_form_selector).html('<iframe width="100%" height="150" frameborder="0" \
                    src="' + o.base_url + '/comment/login?' + qs + '" allowtransparency="true" \
                    vspace="0" hspace="0" marginheight="0" marginwidth="0" id="ds-input-loginform" ></iframe>');
            }
            $(o.input_form_selector +','+ o.logon_form_link).hide();
            $(o.logon_form_selector+','+ o.logon_form_cancel).show();
        },
        hideLogon: function() {
            var self = this; var o = this.defaults;
            $(o.input_form_selector +','+ o.logon_form_link).show();
            $(o.logon_form_selector+','+ o.logon_form_cancel).hide();
        },
        make_url: function(action,include_url){
            var result = $.ds.parseUri(window.location.href);
            var url = this.defaults.base_url + action +'/' + encodeURIComponent(this.defaults.site_slug) + '?';
            //?site_slug=
            url += $.param({ref_url:(result.protocol + '://' + result.authority + result.relative),
                            site_slug: this.defaults.site_slug});
            //post_vals = $.extend({},{ref_url:(result.protocol + '://' + result.authority + result.relative)});
            return url;
        },
        dsactivity: function(options) {
            var opts = $.extend({
                use_url:false,
                activity:null,
                absolute:false,
                unique_id:null,
                category:null,
                custom:null
            },options); 
            var ref_url = '';
            var result = $.ds.parseUri(window.location.href);
            var post_vals = {};
            var url = this.make_url('/apipublic/activity',true);
            if (opts.use_url == true){
                if (opts.absolute == true) {
                    opts.activity = result.protocol + '://' + result.authority;
                }
                opts.activity += result.relative;
            }
            url += '&activity=' + encodeURIComponent(opts.activity);
            post_vals = $.extend(post_vals,{activity:opts.activity});
            if (opts.unique_id != null) {
                post_vals = $.extend(post_vals,{unique_id:opts.unique_id});
            };
            if (opts.category != null) {
                post_vals = $.extend(post_vals,{category:opts.category});
            };
            if (opts.custom != null) {
                var cnames = '';
                for (var name in opts.custom){
                    cnames += name + ',';
                    post_vals[name] = opts.custom[name];
                }
                post_vals = $.extend(post_vals,{'cnames':cnames});
            };
            if (opts.activity != null) {
                $.getJSON(url + '&jsoncallback=?', $.param(post_vals), function(json){});
            };
        }
    });
    
    $.fn.dsactivity = function(options) {
        var defaults = {};
        
        // Extend our default options with those provided.
        var opts = $.extend(defaults, options);
        this.each(function() {
            //if (!$(this).is(".ds-activity")) new $.ds.activity(this, o);
            var jqthis = $(this);
            jqthis.click(function() {
                if (jqthis.attr('activity')) {
                    opts.activity = jqthis.attr('activity');
                    $.ds.dsactivity(opts);
                } else {
                    // what to do?
                    opts.activity = this.textContent;
                    $.ds.dsactivity(opts);
                };
            });
            jqthis.submit(function() {
                alert('in submit of form activity')
                //$.ds.dsactivity(options)
            });
        });
    };
    
    $.fn.dspoll = function(options) {
        return this.each(function() {
               if (!$(this).is(".ds-dspoll")) new $.ds.dspoll(this, options);
        });
    };
    $.ds.dspoll = function(el, options) {
        var opts = $.extend({view_selector:'#ds-poll-results-target',
            poll_id:0,
            getremote:''}, 
            $.ds.defaults, options);
        this.element = el; 
        this.poll_id = $('#poll_id').val();
        this.q_id = $('#q_id').val();
        var self = this; //Do bindings
        self.options = opts;
        if (opts.getremote !== ''){
            self.display(el,opts.getremote);
        }
        $('div.ds-poll-vote a').click(function(){
            self.show_results();
        });
        //#ds-poll-vote
        $('div.ds-poll-vote input').click(function(){
            self.vote(this);
        });
        return this;
    }
    $.extend($.ds.dspoll.prototype, {
        show_results: function(el){
            $('div.ds-poll-vote,#ds-poll-question').hide();
            $(this.options.view_selector).show();
            $(this.options.view_selector).html($('#ds-poll-results').html());
            return this;
        },
        vote: function(el) {
            var self = this;
            var opts = $('#ds-poll-question div input[@checked]').val();
            var data = {poll_id:self.poll_id,q_id:this.q_id,'options':opts};
            //data: $.param(post_vals),
            var url = self.options.base_url + "/pollpublic/vote";
            $.getJSON(url + '?jsoncallback=?', data, function(json){
                $('#ds-poll-results').empty();
                $(self.element).after(json.html);
                self.show_results();
                $.ds.dsactivity({activity:"User Voted On" + json.key,category:"Poll"});
            });
            
        },
        display: function(el,resource_id){
            var self = this;
            var url = this.options.base_url + "/pollpublic/display/" + resource_id;
            $.getJSON(url + '?jsoncallback=?', {}, function(json){
                $(el).append(json.html);
                if ($.browser.safari) {
                    $('style',$(el)).each(function(){
                        $('head').append('<style id="injectedCss" type="text/css">' + $(this).text() + '</style>');
                        $(this).text('');
                    });
                }
            });
        }
    });
    $.fn.dshints = function(el,options) {
        var opts = $.extend({
            hint_selector: '.hint',
            hint_class: 'hint'
        }, options);
        
        //$("input:text[@class=textInput]");
        $(opts.hint_selector,this).each(function() {
            $(this).attr('hint',$(this).val());
        });
        $(opts.hint_selector,this).focus(function(){
            if ($(this).hasClass(opts.hint_class)) {
                $(this).val('').removeClass(opts.hint_class);
            }
        });
        $(opts.hint_selector,this).blur(function(){
            if ($(this).val() == '') {
                $(this).val($(this).attr('hint')).addClass(opts.hint_class);
            }
        });
        $(this).submit(function() {
            $(opts.hint_selector,this).each(function() {
                if ($(this).val() == $(this).attr('hint')) {
                    $(this).val('');
                }
            });
        });
    };
    
    $.fn.comments = function(o) {
        return this.each(function() {
            if (!$(this).is(".ds-comments")) new $.ds.comments(this, o);
        });
    }
    $.ds.comments = function(el, o) {
        var options = {};
        $.ds.defaults.current_url = window.location.href;
        o = o || {}; $.extend(options, $.ds.defaults, o); //Extend and copy options
        this.element = el; var self = this; //Do bindings
        $.data(this.element, "ds-comments", this);
        self.options = options;
        $.ds.prepLogon(this.element);
    }
    
    $.fn.dsgroupac = function(options) {
        
        
        
    };
    $.fn.dshelp = function(options) {
        
        options = $.ds.faceboxmanager.prepare_help_facebox(options);
        
        return this.each(function() {
            if (!$(this).is(".ds-help")) new $.ds.help(this, options);
        });
        
    };
    
    $.ds.faceboxmanager = {
        defaults : {
            style: 'facebox',
            rating: true,
            feedback: true,
            draggable: true,
            topinfo: true,
            resizable: true,
            script: false,
            content: {},
            use_current_url: false,
            source_url:  '',
            url: '', // original url of click
            help_url: '/api/script/help/root/help',
            faceboxprecontent: '#facebox_precontent_holder',
            faceboxcontent: '#facebox_content_holder',
            faceboxcontent2: '#facebox_content_holder2',
            isshown: false,
            isinitialized: false
        },
        groupac: function(){
            //var h = this.get_groupac();
            jQuery.facebox(this.get_groupac());
        },
        load: function(resource_id,content) {
            if (resource_id in this.defaults.content){
                alert('already here' + content);
            } else {
                this.defaults.content[resource_id] = content;
            }
            //$.facebox.reveal(content, 'dshelp',resource_id);
        },
        get_groupac: function() {
            var self = this;
            var qs = 'site_key&' + $.ds.defaults.site_slug; 
            qs += '&url=' + self.defaults.url; 
            return '<div id="ds-inputform-div"><iframe width="100%" height="390" frameborder="0" \
            src="' + $.ds.defaults.base_url + '/groupadmin/popup/' + $.ds.defaults.site_slug +'?' + qs + '"  \
            allowtransparency="true" vspace="0" hspace="0" marginheight="0" marginwidth="0" \
            name="ds-input-form"></iframe></div>';
        },
        prepare_help_facebox: function(options) {
            var opts = $.extend({}, this.defaults, options);
            var self = this; 
            self.options = opts;
            
            if (opts.use_current_url == true){
                opts.script = true,
                result = $.ds.parseUri(window.location.href);
                opts.source_url = $.ds.defaults.base_url + opts.help_url + result.relative;
                opts.url = result.relative;
            }
            if (typeof($.hotkeys) != 'undefined'){
                // hot keys for help
                $.hotkeys.add('Shift+?',{disableInInput: true,type:'keypress'}, function(){ 
                    if ($.facebox.settings.isshown == false) {
                        $.facebox.settings.isshown = true;
                        $('#facebox_show_href').trigger('click');
                        //jQuery(document).trigger('close.facebox')
                    } else {
                        $.facebox.settings.isshown = false;
                        $('#facebox .close').trigger('click');
                    }
                });
            }
            return opts;
        }
    };
    
    $.ds.help = function(el, options) {
        var opts = $.extend({isloaded:false}, $.ds.faceboxmanager.defaults, options);
        this.element = el; 
        var self = this; //Do bindings
        self.options = opts;
        if (opts.style == 'facebox'){
            var fb = $(el).facebox(opts);
        }
        $(el).bind('loaded_script', function() { 
            self.load_content();
        });
        return fb;
    }
    
    $.extend($.ds.help.prototype, {
        load_content: function(resource_id) {
            var self = this;
            // now populate facebox
            if (self.options.isloaded == false) {
                self.options.isloaded = true;
            }
            if (self.options.topinfo) {
                $(self.options.faceboxprecontent).append(self.topinfo());
            }
            if (self.options.rating) {
                $(self.options.faceboxcontent2).append(self.rating());
                var isclicked = false;
                $('.rating input',$(self.options.faceboxcontent2)).click(function(){
                    if (isclicked === false){
                        self.rate(this);
                    }
                })
            }
            if (self.options.feedback) {
                $(self.options.faceboxcontent2).append(self.feedback());
                $.ds.prepLogon($(self.options.faceboxcontent2));
            }
        },
        rate: function (el){
            var self = this;
            var rid = $('#ds-cms-collection').attr('rid');
            var rating_val = ($(el).val() === 'Yes') ? '1': '-1';
              $(el).parent().parent().hide();
            var url = $.ds.make_url('/help/ratearticle',true);
            $.getJSON(url + '&jsoncallback=?', {resource_id:rid,rating:rating_val}, function(json){
                $.ds.dsactivity({activity:"User submitted Help" ,category:"Help"});
            });
        },
        topinfo: function() {
            return '<div class="help-header" style="float:right;"> \
                <img style="vertical-align: top;" src="http://www.demisauce.com/images/icon_help.png" alt="Help" /> \
            </div>';
        },
        rating: function() {
            return '<div class="rating" style="text-align:right;margin:10px 0 0 0;"> \
                <h4>Was This Information Helpful?</h4> \
                <form>\
                        <input id="helpful_yes" class="buttonx" type="button"  value="Yes" name="helpful"/> \
                        <input id="helpful_no" class="buttonx" type="button"  value="No" name="helpful"/> \
                </form></div>';
        },
        feedback: function(txt) {
            var self = this;
            var qs = 'site_key&' + $.ds.defaults.site_slug; 
            qs += '&url=' + self.options.url; 
            return '<div id="ds-inputform-div"><iframe width="100%" height="200" frameborder="0" \
            src="' + $.ds.defaults.base_url + '/help/feedback/' + $.ds.defaults.site_slug +'?' + qs + '"  \
            allowtransparency="true" vspace="0" hspace="0" marginheight="0" marginwidth="0" \
            name="ds-input-form"></iframe></div>';
        },
        hideHelp: function() {
            var self = this;
            self.options.isshown = false;
            $(self.options.helpselector).hide();
        },
        showHelp: function() {
            var self = this;
            $(self.options.helpselector).show();
            $.hotkeys.add('Esc',{disableInInput: true}, function(){ 
                self.hideHelp();
            });
            // setup help close icons
            $("a.close_help,a.demisauce-close-help").click(function(){ 
                self.hideHelp();
            });
            self.options.isshown = true;
        }
    });
})(jQuery);
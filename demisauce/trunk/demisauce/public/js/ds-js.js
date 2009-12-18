(function($){
/*
 * Demisauce Core admin Javascript:  these are core internal javascript
 * components used only for DS admin server.  The client pieces that
 * would go on apps that utilize services are in the ds.client.{plugin}.js
 *
*/
    $.extend($.fn, {
        swapClass: function(c1, c2) {
            return this.each(function() {
                var $this = $(this);
                if ( $.className.has(this, c1) )
                    $this.removeClass(c1).addClass(c2);
                else if ( $.className.has(this, c2) )
                    $this.removeClass(c2).addClass(c1);
            });
        }
    });


    $(document).ready(function() {
        $('.demisauce_help_tip').tooltip({ track: true, delay: 0, showURL: false, 
            showBody: " - ", opacity: 0.90,width: 260});
        $('form').dshints();
    });
    
        
    /*
     * Generic Default static add UI message
     */
    $.extend($, {
         showmessage: function(msg) {
             $.ds.humanMsg.displayMsg(msg);
             //$("#hiddenmessage div:nth-child(2)").html(msg);
             //$("#hiddenmessage").animate({height: 'toggle',opacity: 'toggle'},{duration: 4000});
         }
    });
    //If the Demisauce scope is not availalable, add it
    $.ds = $.ds || {};
    
    /*
    *  Demisauce CMS Email Web Admin
    */
    $.fn.emailadmin = function(o) {
        return this.each(function() {
            if (!$(this).is(".ds-emailadmin")) new $.ds.emailadmin(this, o);
        });
    }
    $.ds.emailadmin = function(el, o) {
        var options = {
            currentfolder: null,
        };
        o = o || {}; $.extend(options, o); //Extend and copy options
        this.element = el; var self = this; //Do bindings
        self.options = options;
        $('a.cmsedit').click(function(){
            self.edit(this);
        });
        $.data(this.element, "ds-emailadmin", this);
    }
    $.extend($.ds.emailadmin.prototype, {
        edit: function (el) {
            var id = $(el).attr('objid');
            alert(' in email edit');
            if (id > 0) {
                $.get("/email/edit/" + id, function(data){
                    $("#EmailItemFormWrapper").html(data);
                });
            }
        }
    });
    $.fn.ds_tabs = function(options) {
        return this.each(function() {
            if (!$(this).is(".ds-tab")) new $.ds.tab(this, options);
        });
    };
    $.ds.tab = function(el, options) {
        $('a',$(el)).click(function() {
            //var currentTab = '#tab1';
            $(this).parent().children('.current').each(function(i) {
                currentTab = this.hash;
            });
            $(this).parent().children().each(function(i) {
                $(this).removeClass('current');
            });
            $(currentTab).hide();
            $(this.hash).show();
            $(this).addClass('current');
        });
    }
    $.fn.ds_poll_admin = function(options) {
        return this.each(function() {
            if (!$(this).is(".ds-poll-admin")) new $.ds.polladmin(this, options);
        });
    };
    $.ds.polladmin = function(el, options) {
        var self = this; 
        self.options = $.extend({isloaded:false,
            q_ids:[],
            id:0,
            permalink_sel: '#real_permalink',
            qoption_html:'<div><label for="option"></label> \
                            <img src="/static/images/move.png" border="0" style="border:0"/> \
                            <input id="question_option" class="tempforjq" o_id="0" name="question_option" style="width:350px" type="text" value="" /> \
                            <img src="/static/images/cross.png" border="0" style="border:0" class="delete"/></div> ',
                    }, options);
        this.element = el; 

        $('#name').focus();
        self.options.q_ids = $('#q_ids').val().split(',');
        $('#question_options div').sortable({items:'div',stop:self.option_sort_complete});

        $('#question_options div div input[o_id=0]').blur(function(){
            if ($(this).val() != ''){
                self.add_option(this);
            } else {
                self.remove_option(this);
            }
        });
        $('#question_options div div[type=other] input').each(function(){
            $(this).attr("disabled", "disabled").next('img.delete').attr('src','');
        });
        $('#name,#question').each(function(){
            $(this).attr('originalval',$(this).val());
        });

        $('#question_options div div input').blur(function(){
            if ($(this).attr('originalval') != $(this).val()){
                self.option_update(this);
                $(this).attr('originalval',$(this).val());
            }
        }).not('input[o_id=0]').each(function(){
            $(this).attr('originalval',$(this).val());
        });
        $('img.delete').not('input[o_id=0]').click(function(){
            self.delete_option(this);
        });
        $('#question').blur(function(){
            self.question_update(this);
        });
        $('form input[name=question_type]').click(function(){
            if($(this).val() == 'radiowother'){
                self.add_option($('#question_options div div input:last'),'other')
            } else if ($(this).val() == 'radio'){
                $('#question_options div div[type=other]').empty();
            } else if ($(this).val() == 'multiplechoice'){
                $('#question_options div div[type=other]').empty();
            }

        });
        $('#jq_add_question').click(function(){
            $('#placeholder_for_newq').before(self.options.qoption_html);
        });
    }

    $.extend($.ds.polladmin.prototype, {
        add_option: function(element,other) {
            var self = this;
            if (other == undefined){
                $(element).parent().parent().append(self.options.qoption_html);
            } else {
                $(element).parent().after(self.options.qoption_html);
                $('#question_options div div input.tempforjq:first').val('other').
                    attr('disabled','disabled').parent().attr('type','other');
            }

            $('#question_options div').sortable({items:'div',stop:self.option_sort_complete});
            $('#question_options div div input.tempforjq').blur(function(){
                self.add_option(this);
            }).removeClass('tempforjq').next().click(function(){
                self.delete_option(this);
            });
            $(element,'~ input').focus();
        },
        remove_option: function(element) {
            $(element,'~ input').parent().empty();
            $('#question_options div div:last').empty();
        },
        option_sort_complete: function(event,ui) {
            var ol = Array(); 
            $('#question_options div div input').each(function(){
                 ol.push('o_id='+$(this).attr('o_id'));
            });
            var d = $('#question_options div div input,#poll_id,#question_options div div input').fieldSerialize();
            d += '&' + ol.join('&') + '&q_id=' + $(this).parent().attr('q_id');
            $.post("/poll/sort/", d, function(msg){
                $.showmessage( "sort completed: ");
            }, "json");
        },
        option_update: function(option) {
            var data = { poll_id: $('#poll_id').val(), 
                question_option: $(option).val(),
                o_id: $(option).attr('o_id'),
                q_id: $(option).parent().parent().attr('q_id'),};
            $.post("/poll/optionupdate/", data, function(msg){
                    //$.showmessage( "update completed: ");
                    if ($(option).attr('o_id') == 0){
                        $(option).attr('o_id',msg.o_id)
                    }
            }, "json");
        },
        delete_option: function(option) {
            var oid = $(option).parent().children('input').attr('o_id');
            if (oid != 0){
                $.post("/poll/delete/", { oid: oid}, function(msg){
                    $.showmessage( " " + msg.msg );
                 }, "json");
            }
            $(option).parent().empty();
        },
        question_added: function(element,id) {
            $(element).attr('q_id',id);
            if ($.inArray(id,this.options.q_ids == -1)){
                this.options.q_ids.push(id);
                $('#q_ids').val(this.options.q_ids.toString());
            }
        },
        question_update: function(element) {
            var self = this;
            if ($(element).val() != '' && $(element).attr('originalval') != $(element).val()){
                var data = { poll_id: $('#poll_id').val(), 
                    option: $('#question_option').fieldSerialize(),
                    name: $('#name').val(),
                    key: $(self.options.permalink_sel).val(),
                    question:$('#question').val(),
                    q_id: $(element).attr('q_id'),};
                $.post("/poll/postquestion/", data, function(msg){
                    $.showmessage( "Data Saved: " + msg.poll.id );
                    if (msg.poll.id > 0 && $('#poll_id').val() == 0){
                        $('#poll_id').val(msg.poll.id);
                        self.options.id = msg.poll.id;
                        self.question_added(element,msg.poll.q_id)
                    }
                }, "json");
            }
        }
    });
    /*
    *  Demisauce CMS Admin page plugin
    */
    $.fn.cmsadmin = function(o) {
        return this.each(function() {
            if (!$(this).is(".ds-cmsadmin")) new $.ds.cmsadmin(this, o);
        });
    }
    $.ds.cmsadmin = function(el, o) {
        var options = {
            currentfolder: null,
        };
        o = o || {}; $.extend(options, o); //Extend and copy options
        this.element = el; var self = this; //Do bindings
        self.options = options;
        $.data(this.element, "ds-cmsadmin", this);
        //$('a.folderlink').treenode({fake:'not'});
        $('a.folderlink,a.folder.empty').click(function(){
            $('.activefolder').removeClass('activefolder');
            $(this).parent().addClass('activefolder');
            self.folderview(this);
        });
        $('span.file').click(function(){
            self.edit(this);
        });
    }
    $.extend($.ds.cmsadmin.prototype, {
        edit: function (el) {
            var self = this;
            var id = $(el).attr('objid');
            $('.activefolder').removeClass('activefolder');
            $(el).addClass('activefolder');
            $.get("/cms/edit/" + id, function(data){
                $("#CmsItemFormWrapper").html(data);
                self.formsetup();
            });
        },
        formsetup: function () {
            $('#cmsform').submit(function() {
                var item_type = $('#item_type').val();
                var title = $('#title').val();
                var id = $('#objectid').val();
                var parentid = $('#parentid').val();
                var newid = 0;
                $(this).ajaxSubmit({success: function(responseText, statusText)  {
                    if (statusText == "success") {
                        newid = responseText;
                        $.showmessage('Item Updated  ' + newid);
                    } else {
                        $.showmessage('There was an error  ' );
                    }
                }});
                var branches = ''; var branche = '';
                //alert('item_type= ' + item_type +  '  id= ' +  id + ' newid= ' + newid);
                $('body').attr('fake',newid);// newid is in a different javascript thread above
                // in ajax, wait for it???
                if (item_type == 'folder' && id == 0) {
                    branches = '<li>' +
                        '<span class="folder empty"  id="item' + newid + '" objid="' + newid + '">' + 
                        '<a href="javascript:void(0);" objid="' + newid + '" class="folderlink" src="">' +
                        title + '</a></span><ul id="cmsitem_' + newid + '"></ul></li>';
                        branche = $(branches).appendTo("#cmsitem_" + parentid);
                }else if (item_type == 'cms' && id == 0) {
                    // new cms item
                    branches = '<li class="last"><span id="item' + newid + '" class="file" objid="' + newid +
                        '">' + title + '</span></li>';
                    alert(branches)
                    $('#list'+parentid).children().removeClass('last');
                    branche = $(branches).appendTo("#list" + parentid);
                }else if (id > 0) {
                    // update title
                    $('#item'+id).html(title);
                }else{
                    // ??
                }
                if (id == 0) { // if it was new, update tree view
                    $("#ContentContextTree").treeview({
                        add: branche
                    });
               }
                return false;
            });
        },
        folderview: function (el) {
            var self = this;
            //remove any current active folders
            var id = $(el).attr('objid');
            $.get("/cms/viewfolder/" + id, function(data){
                $("#CmsItemFormWrapper").html(data).attr('objid',id);
                //$('#actionbar a').removeClass('current');
                $('#addcontentitem').click(function(){
                    self.cmsadd(this);
                });
                $('#addfolder').click(function(){
                    self.addfolder();
                });
                $('#editfolder').click(function(){
                    self.editfolder($('#editfolder'));
                });
                $('#sorttab').click(self.sorttab);
                $("#nodechildrenlist").sortable({stop:self.sortcomplete});
            });
        },
        /*
         * sort tab
         */
        sorttab: function () {
            $('div.boxlinks a').removeClass('current');
            $('#sorttab').addClass('current');
        },
        /*
         * Called on js completion of sort of nodes event
         */
        sortcomplete: function (event,ui) {
            var ss = '';
            $("#nodechildrenlist > li").each(function() {
                ss += $(this).attr('objid') + ',';
            });
            var folderid = $("#nodechildrenlist").attr('objid');
            $.ajax({type: "POST",url: "/cms/reorder/" + folderid ,
                data: "ids=" + ss,
                success: function(msg){
                    $.showmessage( "Data Saved: " + msg );
                }
            });
        },
        addfolder: function () {
            var self = this;
            $('div.boxlinks a').removeClass('current');
            $('#addfolder').addClass('current');
            var parentid = $("#CmsItemFormWrapper").attr('objid');
            if (parentid > 0) {
                $.get("/cms/addfolder/" + parentid, function(data){
                    $("#cmsformtarget").html(data);
                    self.formsetup();
                    $('#title').focus();
                    $('#parentid').val(parentid)
                });
            }else{
                alert('whoops, no parentid')
            }
        },
        cmsadd: function (el) {
            var self = this;
            $('div.boxlinks a').removeClass('current');
            $('#addcontentitem').addClass('current');
            var parentid = $(el).attr('objid');
            if (parentid > 0) {
                $.get("/cms/additem/", function(data){
                    $("#cmsformtarget").html(data);
                    $('#title').focus();
                    $('#parentid').val(parentid)
                    self.formsetup();
                });
            }
        },
        editfolder: function (el) {
            var self = this;
            $('div.boxlinks a').removeClass('current');
            $('#editfolder').addClass('current');
            var folderid = $(el).attr('objid');
            if (folderid > 0) {
                $.get("/cms/edit/" + folderid, function(data){
                    $("#cmsformtarget").html(data);
                    self.formsetup();
                });
            }
        }
    });
    
    /*
        HUMANIZED MESSAGES 1.0
        idea - http://www.humanized.com/weblog/2006/09/11/monolog_boxes_and_transparent_messages
        home - http://humanmsg.googlecode.com
    */
    $.ds.humanMsg = {
        msgId: 'humanMsg',
        msgOpacity: .8,
        tmin: 1500,
        tmax: 5000,
        t2: 5000,  // before you remove by default
        t1: 700, // before you face on mouse/keyboard
        removeMsg: null,
        setup: function(appendTo, msgOpacity) {
            this.msgID = 'humanMsg';
            
            // appendTo is the element the msg is appended to
            if (appendTo == undefined)
                appendTo = 'body';
            
            // Opacity of the message
            this.msgOpacity = .8;
            if (msgOpacity != undefined) 
                this.msgOpacity = parseFloat(msgOpacity);
            
            // Inject the message structure
            jQuery(appendTo).append('<div id="'+this.msgID+'" class="humanMsg"><div class="round"></div><p></p><div class="round"></div></div>');
        },
        displayMsg: function(msg) {
            if (msg == '')
                return;
            
            clearTimeout(this.t2);
            
            // Inject message
            jQuery('#'+this.msgID+' p').html(msg)
            
            // Show message
            jQuery('#'+this.msgID+'').show().animate({ opacity: this.msgOpacity});
            
            // Watch for mouse & keyboard in .5s
            this.t1 = setTimeout("$.ds.humanMsg.bindEvents()", this.tmin)
            // Remove message after 5s
            this.t2 = setTimeout("$.ds.humanMsg.removeMsg()", this.tmax)
        },
        bindEvents: function() {
            // Remove message if mouse is moved or key is pressed
            jQuery(window)
                .mousemove(this.removeMsg)
                .click(this.removeMsg)
                .keypress(this.removeMsg);
        },
        removeMsg: function() {
            // Unbind mouse & keyboard
            var self = $.ds.humanMsg;
            jQuery(window)
                .unbind('mousemove', self.removeMsg)
                .unbind('click', self.removeMsg)
                .unbind('keypress', self.removeMsg);
            
            // If message is fully transparent, fade it out
            if (jQuery('#'+self.msgID).css('opacity') == self.msgOpacity) {
                jQuery('#'+self.msgID).animate({ opacity: 0 }, 500, function() {
                     jQuery(this).hide() 
                });
            }
        }
    }

})(jQuery);

jQuery(document).ready(function(){
    $.ds.humanMsg.setup();
})
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
            if (str == undefined){
                str = window.location.href;
            }
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
            use_sub_domains : false,
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
                var qs = 'url=' + encodeURIComponent(window.location.href);
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
        service_url: function(action,include_url){
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
            var url = this.service_url('/apipublic/activity',true);
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
                $.getJSON(url + '&jsoncallback=?', $.param(post_vals), function(json){
                    alert('success or failure?' + json)
                });
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
               if (!$(this).is("ds-dspoll")) new $.ds.dspoll(this, options);
        });
    };
    $.ds.dspoll = function(el, options) {
        var opts = $.extend({view_selector:'.ds-poll-results-target',
            poll_id:0,
            getremote:''}, 
            $.ds.defaults, options);
        this.element = el; 
        var self = this; 
        this.poll_id = $('#poll_id',$(self.element)).val();
        this.q_id = $('#q_id',$(self.element)).val();
        self.options = opts;
        $.data(this.element, "ds-dspoll", this);
        if (opts.getremote !== ''){
            self.display(el,opts.getremote);
        }
        $('div.ds-poll-vote a',$(self.element)).click(function(){
            self.show_results();
        });
        //#ds-poll-vote
        $('div.ds-poll-vote input',$(self.element)).click(function(){
            self.vote(this);
        });
        return this;
    }
    $.extend($.ds.dspoll.prototype, {
        show_results: function(el){
            var self = this;
            $('div.ds-poll-vote,.ds-poll-question',$(self.element)).hide();
            $(this.options.view_selector,$(self.element)).children().show();
            $('#ds-poll-results-' + self.poll_id).show();
            return this;
        },
        vote: function(el) {
            var self = this;
            var opts = $('.ds-poll-question div input[@checked]',$(self.element)).val();
            var data = {poll_id:self.poll_id,q_id:this.q_id,'options':opts};
            //data: $.param(post_vals),
            var url = self.options.base_url + "/pollpublic/vote";
            $.getJSON(url + '?jsoncallback=?', data, function(json){
                //$('#ds-poll-results-' +self.poll_id).empty();// fails on cross domain
                $(self.element).hide();
                $(self.element).after(json.html);
                $('#' +json.htmlid).show();
                $.ds.dsactivity({activity:"User Voted On" + json.key,category:"Poll"});
            });
            
        },
        display: function(el,resource_id){
            var self = this;
            var url = this.options.base_url + "/pollpublic/display/" + resource_id;
            $.getJSON(url + '?jsoncallback=?', {}, function(json){
                $(el).append(json.html);
                if (self.options.success){
                    self.options.success();
                }
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
            if ($(this).hasClass(opts.hint_class) &&
                    ($(this).val() == $(this).attr('hint'))) {
                $(this).val('');
                $(this).removeClass(opts.hint_class);
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
        var options = {commentiframe:true};
        $.ds.defaults.current_url = window.location.href;
        o = o || {}; $.extend(options, $.ds.defaults, o); //Extend and copy options
        this.element = el; var self = this; //Do bindings
        $.data(this.element, "ds-comments", this);
        self.options = options;
        $.ds.prepLogon(this.element);
        if (o.commentiframe === false){
            $($.ds.defaults.logon_form_link).click(function(){
                $.ds.showLogon();
                $('#ds-commentform-div',$(self.element)).hide();
            });
            $($.ds.defaults.logon_form_cancel).click(function(){
                $('#ds-commentform-div',$(self.element)).show();
            });
            $('#commentform').submit(function() { 
                var qs = $(this).formSerialize(); 
                var url = $.ds.defaults.base_url + '/comment/commentsubmitjsonp/${c.site.slug}?jsoncallback=?&' + qs;
                $.getJSON(url , {}, function(json){
                    $('#ds-commentform-div').html(json.html);
                });
                return false;
            });
        }
        
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
            rating: false,
            feedback: true,
            draggable: true,
            topinfo: false,
            resizable: true,
            script: false,
            content: {},
            use_current_url: false,
            source_url:  '',
            url: '', // original url of click
            help_url: '/api/json/help/root/help',
            help_popup_url:'/help/submitfeedback',
            faceboxprecontent: '#facebox_precontent_holder',
            faceboxcontent: '#facebox_content_holder',
            faceboxcontent2: '#facebox_content_holder2',
            isshown: false,
            isinitialized: false
        },
        groupac: function(){
            //var h = this.get_groupac();
            jQuery.facebox(this.get_groupac());
            // since its an iframe
            $('#facebox .content').before('<div id="facebox_precontent_holder"></div>');
            $('#facebox').css({left:((window.innerWidth - 670)/2),width:670,height:500});
            $('#facebox_precontent_holder').css({width:630});
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
            return '<div id="ds-inputform-div"><iframe width="100%" height="420" width="570" frameborder="0" \
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
                opts.url = $.ds.defaults.base_url + opts.help_url + result.relative.replace('#','');
                opts.source_url = result.relative;
            }
            return opts;
        }
    };
    
    $.ds.help = function(el, options) {
        var opts = $.extend({isloaded:false,
            hotkeys:false,showtitle:false}, $.ds.faceboxmanager.defaults, options);
        this.element = el; 
        var self = this; //Do bindings
        self.options = opts;
        
        var temp = (opts.style === 'facebox');// what hack is this?  why does it fail?
        if ((opts.style === 'facebox')){
            $(el).click(function(){
                self.load_content();
                return false;
            });
            if (opts.hotkeys === true){
                if (typeof($.hotkeys) != 'undefined'){
                    // hot keys for help
                    $.hotkeys.add('Shift+?',{disableInInput: true,type:'keypress'}, function(){ 
                        if ($.facebox.settings.isshown == false) {
                            self.load_content();
                        } else {
                            $.facebox.settings.isshown = false;
                            $('#facebox .close').trigger('click');
                        }
                    });
                }
            }
        } else if (opts.style == 'popup'){
            $(el).click(function(){
                var result = $.ds.parseUri(window.location.href);
                var url = $.ds.defaults.base_url + opts.help_popup_url +'/' + encodeURIComponent($.ds.defaults.site_slug) + '?';
                url += $.param({ref_url:(result.protocol + '://' + result.authority + result.relative),
                                site_slug: $.ds.defaults.site_slug});
                 window.open (url,"mywindow","location=1,status=1,scrollbars=1,width=500,height=400");
            });
        }
        return this;
    }
    
    $.extend($.ds.help.prototype, {
        load_content: function() {
            var self = this;
            $.facebox.loading();
            if (self.options.isloaded === false && self.options.topinfo){
                $.getJSON(self.options.url + '?jsoncallback=?', {}, function(json){
                      self.topcontent = json.html;
                      self.options.isloaded = true;
                      $(self.options.faceboxprecontent).append(self.topcontent);
                });
            }
            jQuery.facebox('');
            if (typeof $.fn.draggable != 'undefined'){
                $('#facebox').draggable();
            }
            
            $(document).bind('close.facebox', function() { 
                self.on_close();
                $('#facebox_precontent_holder').remove();
                $('#facebox_content_holder2').remove();
                $('#facebook_esc_close').remove();
            });
            $('#facebox .content').before('<div id="facebox_precontent_holder"></div>');
            $('#facebox .content').after('<div id="facebox_content_holder2"></div>');
            $('#facebox .footer').prepend('<span id="facebook_esc_close" class="" style="float:left;text-align:left;">ESC = Close this panel</span>');

            // now populate facebox
            if (self.options.isloaded === false) {
                self.options.isloaded = true;
            }
            $('#facebox').css({left:((window.innerWidth - 670)/2),width:670});
            $('#facebox_precontent_holder').css({width:630});
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
            // convert images to absolute
            $('img',$('#facebox')).each(function (){
                result = $.ds.parseUri(this.src);
                url = $.ds.defaults.base_url + result.relative;
                this.src = url;
            });
            var category = 'help';
            if (self.options.showtitle) {
                category = $(this.element).attr('category');
                $(self.options.faceboxprecontent).append('<h3>' + $(this.element).html() + '</h3>');
            }
            if (self.options.feedback) {
                $(self.options.faceboxcontent2).append(self.feedback(category));
                //$.ds.prepLogon($(self.options.faceboxcontent2));
            }
            $.ds.prepLogon($('#facebox_content_holder2'));
        },
        on_close: function(el){
            
        },
        rate: function (el){
            var self = this;
            var rid = $('#ds-cms-collection').attr('rid');
            var rating_val = ($(el).val() === 'Yes') ? '1': '-1';
              $(el).parent().parent().hide();
            var url = $.ds.service_url('/help/ratearticle',true);
            $.getJSON(url + '&jsoncallback=?', {resource_id:rid,rating:rating_val}, function(json){
                $.ds.dsactivity({activity:"User submitted a rating on help" ,category:"Help"});
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
        feedback: function(category) {
            var self = this;
            var qs = 'site_key=' + $.ds.defaults.site_slug; 
            qs += '&url=' + self.options.url + '&category=' + category; 
            return '<div id="ds-inputform-div" ttestatt="fake" style="width:630;"><iframe width="100%" height="200" frameborder="0" \
            src="' + $.ds.defaults.base_url + '/help/feedback/' + $.ds.defaults.site_slug +'?' + qs + '"  \
            allowtransparency="true" vspace="0" hspace="0" marginheight="0" marginwidth="0" \
            name="ds-input-form"></iframe></div>';
        },
        xxxhideHelp: function() {
            var self = this;
            self.options.isshown = false;
            $(self.options.helpselector).hide();
        },
        xxxxshowHelp: function() {
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
    
    
    $.fn.dstags = function(options) {
        return this.each(function() {
             if (!$(this).is(".ds-tag-helper")) new $.ds.tag_helper(this, options);
        });
    };
    $.ds.tag = {
        defaults: {
            tag_div_selector: '#tag_list_div',
            tagged_class: 'tagged_wdelete',
            tag_input: '#tags',
            id: "tbd"
        }
    };
    $.ds.tag_helper = function(el,options) {
        var self = this;
        options = $.extend({tags:[],tagd:{}}, $.ds.tag.defaults, options);
        self.first_tag = true;
        self.element = el; 
        self.options = options;
        $.data(this.element, ".ds-tag-helper", this);
        var tags = options.tags;
        for (var i=0; i < tags.length; i++) {
            self.add_tag(tags[i]);
        }
        var self = this;
        $('a',$(el)).click(function(){
            self.click_tag($(this).html());
        });
    };
    $.extend($.ds.tag_helper.prototype, {
        add_tag: function(tag){
            var self = this;
            //remove hint
            if (self.first_tag === true){
                $(self.options.tag_input).focus();
                self.first_tag = false;
            }
            // highlight tag
            if (tag.indexOf(':') > 0){
                $('#tag_' + tag.replace(':','')).addClass(self.options.tagged_class);
            } else {
                $('#tag_' + tag).addClass(self.options.tagged_class);
            }
            
            // add to selected list
            if (!(tag in self.options.tagd)){
                self.options.tagd[tag] = tag;
                self.options.tags[self.options.length] = tag;
            }
            // add to input box
            var sep = ',';
            var jqTagInput = $(self.options.tag_input).val();
            if (jqTagInput == '') sep = '';
            $(self.options.tag_input).val(jqTagInput + sep + tag);
        },
        click_tag: function(tag){
            var self = this;
            if (!(tag in self.options.tagd)){
                self.add_tag(tag);
            } else {
                // remove
                delete self.options.tagd[tag]
                var newtags = [];
                for (var t in self.options.tagd) newtags[newtags.length] = t;
                self.options.tags = newtags;
                // remove highlight tag
                if (tag.indexOf(':') > 0){
                    $('#tag_' + tag.replace(':','')).removeClass(self.options.tagged_class);
                } else {
                    $('#tag_' + tag).removeClass(self.options.tagged_class);
                }
                $(self.options.tag_input).val(newtags.join(','));
            }
        }
    });
    
    
})(jQuery);
/**
 * Cookie plugin
 *
 * Copyright (c) 2006 Klaus Hartl (stilbuero.de)
 * Dual licensed under the MIT and GPL licenses:
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.gnu.org/licenses/gpl.html
 *
 */

/**
 * Create a cookie with the given name and value and other optional parameters.
 *
 * @example $.cookie('the_cookie', 'the_value');
 * @desc Set the value of a cookie.
 * @example $.cookie('the_cookie', 'the_value', {expires: 7, path: '/', domain: 'jquery.com', secure: true});
 * @desc Create a cookie with all available options.
 * @example $.cookie('the_cookie', 'the_value');
 * @desc Create a session cookie.
 * @example $.cookie('the_cookie', null);
 * @desc Delete a cookie by passing null as value.
 *
 * @param String name The name of the cookie.
 * @param String value The value of the cookie.
 * @param Object options An object literal containing key/value pairs to provide optional cookie attributes.
 * @option Number|Date expires Either an integer specifying the expiration date from now on in days or a Date object.
 *                             If a negative value is specified (e.g. a date in the past), the cookie will be deleted.
 *                             If set to null or omitted, the cookie will be a session cookie and will not be retained
 *                             when the the browser exits.
 * @option String path The value of the path atribute of the cookie (default: path of page that created the cookie).
 * @option String domain The value of the domain attribute of the cookie (default: domain of page that created the cookie).
 * @option Boolean secure If true, the secure attribute of the cookie will be set and the cookie transmission will
 *                        require a secure protocol (like HTTPS).
 * @type undefined
 *
 * @name $.cookie
 * @cat Plugins/Cookie
 * @author Klaus Hartl/klaus.hartl@stilbuero.de
 */

/**
 * Get the value of a cookie with the given name.
 *
 * @example $.cookie('the_cookie');
 * @desc Get the value of a cookie.
 *
 * @param String name The name of the cookie.
 * @return The value of the cookie.
 * @type String
 *
 * @name $.cookie
 * @cat Plugins/Cookie
 * @author Klaus Hartl/klaus.hartl@stilbuero.de
 */
jQuery.cookie = function(name, value, options) {
    if (typeof value != 'undefined') { // name and value given, set cookie
        options = options || {};
        if (value === null) {
            value = '';
            options.expires = -1;
        }
        var expires = '';
        if (options.expires && (typeof options.expires == 'number' || options.expires.toUTCString)) {
            var date;
            if (typeof options.expires == 'number') {
                date = new Date();
                date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000));
            } else {
                date = options.expires;
            }
            expires = '; expires=' + date.toUTCString(); // use expires attribute, max-age is not supported by IE
        }
        var path = options.path ? '; path=' + options.path : '';
        var domain = options.domain ? '; domain=' + options.domain : '';
        var secure = options.secure ? '; secure' : '';
        document.cookie = [name, '=', encodeURIComponent(value), expires, path, domain, secure].join('');
    } else { // only name given, get cookie
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
};(function($){
/*
/* Demisauce Slug Editor Plugin
 *
 * $Date: 2008-5-25
 * $Author:  Aaron Raddon
*/
    //If the ds scope not available, add it
    $.ds = $.ds || {};

    $.fn.slugeditor = function(o) {
        
        return this.each(function() {
            if (!$(this).is(".ds-slugeditor")) new $.ds.slugeditor(this, o);
        });
    }
    $.ds.slugeditor = function(el, o) {
        var options = {
            permalink_sel: '#real_permalink',
            permalink_span: '#editable-slug-span',
            permalink_edit: '#editable-slug-href',
            permalink_div: '#permalink_div',
            slugfrom: '#title',
            strip: false
        };
        o = o || {}; $.extend(options, o); //Extend and copy options
        this.element = el; var self = this; //Do bindings
        self.options = options;
        $.data(this.element, "ds-slugeditor", this);
        $(options.slugfrom).blur(function(e){
            self.show(this);
        });
        //"#editable-post-name,#editable-post-href"
        $(options.permalink_span + ',' + options.permalink_edit).click(function() {
            self.slugedit(this);
         });
    }
    $.extend($.ds.slugeditor.prototype, {
        slugblur: function (el) {
            var self = this;
            $(self.options.permalink_sel).hide();
            $(self.options.permalink_span).html($(self.options.permalink_sel).val());
        },
        show: function (el) {
            var self = this;
            //$(self.options.permalink_div).show();
            $(self.options.permalink_sel).hide();
            $(self.options.permalink_span).html($(self.options.permalink_sel).val());
            var slug = $(self.options.permalink_sel).val();
            if (slug == '') {
                if (self.options.strip == true) {
                    slug = $(self.options.slugfrom).val().replace(/ /g,'').toLowerCase().replace(/[^a-z\-]/g,'');
                } else {
                    slug = $(self.options.slugfrom).val().replace(/ /g,'-').toLowerCase().replace(/[^a-z\-]/g,'');
                }
                slug = slug.replace(/(-{2,50})/g,'-');
                $(self.options.permalink_sel).val(slug);
            }else{
                
            }
            $(self.options.permalink_span).html(slug);
        },
        slugedit: function (el) {
            var self = this;
            self.show();
            $(self.options.permalink_sel).show().focus();
            $(self.options.permalink_sel).keypress(function(e){
                var key = e.charCode ? e.charCode : e.keyCode ? e.keyCode : 0;
                // Make sure not to save entire form, just slug if the hit return
                if ((13 == key) || (27 == key)) {
                    self.slugblur();
                    return false;
                }
            });
            $(self.options.permalink_sel).blur(function(e){
                $(this).hide();
                $(self.options.permalink_span).html($(this).val());
            });
        }
    });
})(jQuery);// Copyright 2007, Google Inc.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
//  1. Redistributions of source code must retain the above copyright notice,
//     this list of conditions and the following disclaimer.
//  2. Redistributions in binary form must reproduce the above copyright notice,
//     this list of conditions and the following disclaimer in the documentation
//     and/or other materials provided with the distribution.
//  3. Neither the name of Google Inc. nor the names of its contributors may be
//     used to endorse or promote products derived from this software without
//     specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED
// WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
// EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
// PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
// OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
// WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
// OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
// ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
// Sets up google.gears.*, which is *the only* supported way to access Gears.
//
// Circumvent this file at your own risk!
//
// In the future, Gears may automatically define google.gears.* without this
// file. Gears may use these objects to transparently fix bugs and compatibility
// issues. Applications that use the code below will continue to work seamlessly
// when that happens.

(function() {
  // We are already defined. Hooray!
  if (window.google && google.gears) {
    return;
  }

  var factory = null;

  // Firefox
  if (typeof GearsFactory != 'undefined') {
    factory = new GearsFactory();
  } else {
    // IE
    try {
      factory = new ActiveXObject('Gears.Factory');
      // privateSetGlobalObject is only required and supported on WinCE.
      if (factory.getBuildInfo().indexOf('ie_mobile') != -1) {
        factory.privateSetGlobalObject(this);
      }
    } catch (e) {
      // Safari
      if ((typeof navigator.mimeTypes != 'undefined')
           && navigator.mimeTypes["application/x-googlegears"]) {
        factory = document.createElement("object");
        factory.style.display = "none";
        factory.width = 0;
        factory.height = 0;
        factory.type = "application/x-googlegears";
        document.documentElement.appendChild(factory);
      }
    }
  }

  // *Do not* define any objects if Gears is not installed. This mimics the
  // behavior of Gears defining the objects in the future.
  if (!factory) {
    return;
  }

  // Now set up the objects, being careful not to overwrite anything.
  //
  // Note: In Internet Explorer for Windows Mobile, you can't add properties to
  // the window object. However, global objects are automatically added as
  // properties of the window object in all browsers.
  if (!window.google) {
    google = {};
  }

  if (!google.gears) {
    google.gears = {factory: factory};
  }
})();(function($){
    
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
            this.resource_store = this.local_server.createStore(this.resource_store_name);
            var self = this;
            var out_msg = 'now available offline:';
            //$('img,script')
            var files_to_capture = [];
            $('script[gears=true]').each(function (){
                //alert(this.src);
                files_to_capture.push(this.src);
            });
            //alert('before capture' + files_to_capture[0])
            self.resource_store.capture(files_to_capture,function (url,success,captureId){
                //alert('in capture ' + url + + (success ? 'succeeded' : 'failed'))
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
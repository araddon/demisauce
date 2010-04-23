(function($)
{
  if (window['log'] == undefined){
    window['log'] = {
      toggle: function() {},
      move: function() {},
      resize: function() {},
      clear: function() {},
      debug: function() {},
      info: function() {},
      warn: function() {},
      error: function() {},
      profile: function() {}
    };
  }
    //If the Demisauce scope is not availalable, add it
    $.ds = $.ds || {};

    $.extend($.ds, {
        auth: function(user_key) {
          user_ckie = $.cookie('dsuserkey');
          if (user_ckie == undefined || user_ckie == null){
            var url = this.defaults.base_url + '/api/user/' + encodeURIComponent(user_key) + '/init_user?site_slug=' + encodeURIComponent(this.defaults.site_slug) ;
            $.getJSON(url + '&jsoncallback=?', {}, function(json){});
          }
        },
        /*
            parseUri 1.2.1
            (c) 2007 Steven Levithan <stevenlevithan.com>
            http://stevenlevithan.com/demo/parseuri/js/
            MIT License
            
            Demisauce mods:  namespaced it and included here
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
            var url = this.service_url('/api/activity',true);
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
                //+ '&jsoncallback=?'
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
    
    $.fn.dshints = function(el,options) {
      var opts = $.extend({
          hint_selector: '.hint',
          hint_class: 'hint'
      }, options);
      
      var form = this;
      
      //$("input:text[@class=textInput]");
      $(opts.hint_selector,form).each(function() {
          if ($(this).val() == '' && $(this).attr('hint').length > 0) {
            $(this).val($(this).attr('hint'));
          } else if ($(this).val() != ''){
            //$(this).attr('hint',$(this).val());
            $(this).removeClass(opts.hint_class);
          }
          // on focus add/remove class
          $(this).focus(function(){
            if ($(this).hasClass(opts.hint_class) &&
                      ($(this).val() == $(this).attr('hint'))) {
              $(this).val('');
              $(this).removeClass(opts.hint_class);
            }
          }).blur(function(){
            if ($(this).val() == '') {
              $(this).val($(this).attr('hint')).addClass(opts.hint_class);
            }
          });
      });
      $(form).submit(function() {
          $(opts.hint_selector,this).each(function() {
              if ($(this).val() == $(this).attr('hint')) {
                  $(this).val('');
              }
          });
      });
    };
    
    $.fn.dsassetmgr = function(o) {
        return this.each(function() {
            if (!$(this).is(".ds-assetmgr")) new $.ds.assetmanager(this, o);
        });
    }
    $.ds.assetmanager = function(el, o) {
        var options = {commentiframe:true,
            buttonText:'Attach Photo',
            args:'',
            multiple:true,
            oncomplete:on_complete,
            buttonImg : '/static/images/addphoto.png'};
        o = o || {}; $.extend(options, $.ds.defaults, o); //Extend and copy options
        var self = $(el); //Do bindings
        this.element = el; 
        $.data(this.element, "ds-assetmgr", this);
        self.options = options;
        self.after('<div class="uploadifyholder"></div>');
        function on_complete(json){
          if (json.success === true) {
              try {
                  var response = json.response;
                  if (response.indexOf('<h1>413 Request') > 0){
                      $.showmessage( " Sorry, that photo was larger than 6mb, please try a smaller photo or resize it.");
                  } else {
                    if (options.multiple === true){
                      var images = self.val() ? self.val() + ',' + response: response;
                      self.val(images);
                    } else {
                      self.val(response);
                    }
                    $('<div></div>').appendTo($('.uploadifyholder',self.parent())).html(json.filename + "   added <br />");
                  }
              } catch(e) {
                  log.error(e);
              }
          } else {
              log.error("json failed");
              $('<div></div>').appendTo($('.uploadifyholder',self.parent())).html(json.filename + "   Failed <br />");
          }
        }
        //'cancelImg'      : '/static/js/jquery.uploadify-v2.1.0/cancel.png',
        log.debug("setting uploader url to " + $.ds.defaults.base_url + '/upload/')
        $(el).uploadify({
             'uploader'       : $.ds.defaults.base_url +'/static/js/jquery.uploadify-v2.1.0/uploadify.swf',
             'script'         : $.ds.defaults.base_url + '/upload/',
             'cancelImg'      : $.ds.defaults.base_url + '/static/images/close.png',
             'folder'         : '/upload',
             'auto'           : true,
             'scriptData'     : {'args':options.args},
             'multi'          : false,
             'fileDataName'   : 'userfile',
             'hideButton'     : false,
             'buttonText'     : self.options.buttonText,
             'scriptAccess'   : 'always',
             'buttonImg'      : self.options.buttonImg,
             'wmode'          : 'transparent',
             height           : 33, 
             onOpen           :function(){
                log.debug('uploadify onopen');
                self.trigger("onOpen",{});
             },
             'onError':  function (event, queueID ,fileObj, errorObj) {
                   var msg;
                   if (errorObj.status == 404) {
                      msg = 'Could not find upload script.';
                   } else if (errorObj.status == 499) {
                    $('<div></div>').appendTo($('.uploadifyholder',self.parent())).html(fileObj.name + "  Upload Timed Out <br />");
                    return false;
                   } else if (errorObj.type === "HTTP") {
                      msg = errorObj.type+": "+errorObj.status;
                   } else if (errorObj.type ==="File Size") {
                      msg = fileObj.name+'<br>'+errorObj.type+' Limit: '+Math.round(errorObj.sizeLimit/1024)+'KB';
                   } else {
                      msg = errorObj.type+": "+errorObj.text;
                   }
                   //alert(msg);
                   //$("#fileUpload" + queueID).fadeOut(250, function() { $("#fileUpload" + queueID).remove()});
                   $('<div></div>').appendTo($('.uploadifyholder',self.parent())).html(fileObj.name + "  Upload Failed <br />");
                   return false;
             },
            'onComplete': function(event,queueID,fileObj,response){
              var json = {'success':true,'filename':fileObj.name,"response":response};
              options.oncomplete(json);
              self.trigger("onComplete",json);
              return true;
            }
        });
    }
    
    $.fn.modalbox = function(options) {
      options = $.extend({
          content: null,
          width:400,
          cssclass: 'modalbox',
          onload: function(){}
      }, options);
      
      var KEY = {
        ESC: 27,
        AT: 50
      };
      
      if ($('#modalbox').length == 0) {
        $("body").append('<div id="modalbox" class="modalbox" style="display:none;"><div class="modalbox-inner"></div></div>');
        $(".modalbox-inner").css({width:options.width});
        //$("body").append('<div class="modalbox-wrapper" style="display:none;"><div class="modalbox"><div class="modalbox-inner"></div></div></div>');
      }
      
      return this.each(function() {
          var self = $(this);
          self.el = this;
          
          // only opera doesn't trigger keydown multiple times while pressed, others don't work with keypress at all
          self.bind(($.browser.opera ? "keypress" : "keydown"), function(event) {
            var k=event.keyCode || event.which; // keyCode == 0 in Gecko/FF on keypress
            //log.debug("keypress: " + k + ' ' + event.shiftKey)
            switch(k) {
              case KEY.ESC:
                close();
                break;
              default:
                break;
            }
          }).focus(function(){
            
          })
          var cur_content = null;
          var is_loaded = false;
          function load_content(){
            if (options.content) {
              $('.modalbox-inner').html($(options.content).html());
              setup_events();
              options.onload();
            } else if (options.href){
              log.debug("getting " + options.href)
              $.get(options.href, function(data) { 
                $('.modalbox-inner').html(data);
                log.debug("finished loading data");
                setup_events();
                options.onload();
              });
            }
          }
          function close() {
            $('.modalbox').fadeOut(200);
            $('.modalbox-overlay').remove();
          }
          function setup_events(){
            $('.modalbox').before('<div class="modalbox-overlay"></div>');
            $('.modalbox').fadeIn(200);
            $('.modalbox-overlay').live('click',function(){
              log.debug("clicked close overlay");
              self.trigger("modalbox.close",[]);
              close();
            });
            $('.close',$('.modalbox')).live('click',function(){
              log.debug("clicked close2 button/cancel");
              self.trigger("modalbox.close",[]);
              close();
            });
            $('.showtipsy').trigger("cancel-tipsy",[]);
            $('.modalbox').bind('modalbox.close',function(){
              close();
            });
          }
          $(this).click(function(){
            var new_content = options.content ? options.content : options.href;
            if (cur_content != new_content) {
              load_content();
            } else {
              setup_events();
              options.onload();
            }
            cur_content = new_content;
            return false;
          });
      });
    };
    
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
};
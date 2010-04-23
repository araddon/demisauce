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

    //If the Demisauce scope is not availalable, add it
    $.ds = $.ds || {};
    
    $('.demisauce_help_tip').tooltip({ track: true, delay: 0, showURL: false, 
            showBody: " - ", opacity: 0.90,width: 260});
    $('form').dshints();
    
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
            currentfolder: null
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
});

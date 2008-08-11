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
                            <img src="/images/move.png" border="0" style="border:0"/> \
                            <input id="question_option" class="tempforjq" o_id="0" name="question_option" style="width:350px" type="text" value="" /> \
                            <img src="/images/cross.png" border="0" style="border:0" class="delete"/></div> ',
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

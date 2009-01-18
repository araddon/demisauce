(function(a){a.extend(a.fn,{swapClass:function(c,b){return this.each(function(){var d=a(this);if(a.className.has(this,c)){d.removeClass(c).addClass(b)}else{if(a.className.has(this,b)){d.removeClass(b).addClass(c)}}})}});a(document).ready(function(){a(".demisauce_help_tip").tooltip({track:true,delay:0,showURL:false,showBody:" - ",opacity:0.9,width:260});a("form").dshints()});a.extend(a,{showmessage:function(b){a.ds.humanMsg.displayMsg(b)}});a.ds=a.ds||{};a.fn.emailadmin=function(b){return this.each(function(){if(!a(this).is(".ds-emailadmin")){new a.ds.emailadmin(this,b)}})};a.ds.emailadmin=function(d,e){var c={currentfolder:null,};e=e||{};a.extend(c,e);this.element=d;var b=this;b.options=c;a("a.cmsedit").click(function(){b.edit(this)});a.data(this.element,"ds-emailadmin",this)};a.extend(a.ds.emailadmin.prototype,{edit:function(b){var c=a(b).attr("objid");alert(" in email edit");if(c>0){a.get("/email/edit/"+c,function(d){a("#EmailItemFormWrapper").html(d)})}}});a.fn.ds_tabs=function(b){return this.each(function(){if(!a(this).is(".ds-tab")){new a.ds.tab(this,b)}})};a.ds.tab=function(c,b){a("a",a(c)).click(function(){a(this).parent().children(".current").each(function(d){currentTab=this.hash});a(this).parent().children().each(function(d){a(this).removeClass("current")});a(currentTab).hide();a(this.hash).show();a(this).addClass("current")})};a.fn.ds_poll_admin=function(b){return this.each(function(){if(!a(this).is(".ds-poll-admin")){new a.ds.polladmin(this,b)}})};a.ds.polladmin=function(d,c){var b=this;b.options=a.extend({isloaded:false,q_ids:[],id:0,permalink_sel:"#real_permalink",qoption_html:'<div><label for="option"></label>                             <img src="/images/move.png" border="0" style="border:0"/>                             <input id="question_option" class="tempforjq" o_id="0" name="question_option" style="width:350px" type="text" value="" />                             <img src="/images/cross.png" border="0" style="border:0" class="delete"/></div> ',},c);this.element=d;a("#name").focus();b.options.q_ids=a("#q_ids").val().split(",");a("#question_options div").sortable({items:"div",stop:b.option_sort_complete});a("#question_options div div input[o_id=0]").blur(function(){if(a(this).val()!=""){b.add_option(this)}else{b.remove_option(this)}});a("#question_options div div[type=other] input").each(function(){a(this).attr("disabled","disabled").next("img.delete").attr("src","")});a("#name,#question").each(function(){a(this).attr("originalval",a(this).val())});a("#question_options div div input").blur(function(){if(a(this).attr("originalval")!=a(this).val()){b.option_update(this);a(this).attr("originalval",a(this).val())}}).not("input[o_id=0]").each(function(){a(this).attr("originalval",a(this).val())});a("img.delete").not("input[o_id=0]").click(function(){b.delete_option(this)});a("#question").blur(function(){b.question_update(this)});a("form input[name=question_type]").click(function(){if(a(this).val()=="radiowother"){b.add_option(a("#question_options div div input:last"),"other")}else{if(a(this).val()=="radio"){a("#question_options div div[type=other]").empty()}else{if(a(this).val()=="multiplechoice"){a("#question_options div div[type=other]").empty()}}}});a("#jq_add_question").click(function(){a("#placeholder_for_newq").before(b.options.qoption_html)})};a.extend(a.ds.polladmin.prototype,{add_option:function(d,b){var c=this;if(b==undefined){a(d).parent().parent().append(c.options.qoption_html)}else{a(d).parent().after(c.options.qoption_html);a("#question_options div div input.tempforjq:first").val("other").attr("disabled","disabled").parent().attr("type","other")}a("#question_options div").sortable({items:"div",stop:c.option_sort_complete});a("#question_options div div input.tempforjq").blur(function(){c.add_option(this)}).removeClass("tempforjq").next().click(function(){c.delete_option(this)});a(d,"~ input").focus()},remove_option:function(b){a(b,"~ input").parent().empty();a("#question_options div div:last").empty()},option_sort_complete:function(c,e){var b=Array();a("#question_options div div input").each(function(){b.push("o_id="+a(this).attr("o_id"))});var f=a("#question_options div div input,#poll_id,#question_options div div input").fieldSerialize();f+="&"+b.join("&")+"&q_id="+a(this).parent().attr("q_id");a.post("/poll/sort/",f,function(d){a.showmessage("sort completed: ")},"json")},option_update:function(b){var c={poll_id:a("#poll_id").val(),question_option:a(b).val(),o_id:a(b).attr("o_id"),q_id:a(b).parent().parent().attr("q_id"),};a.post("/poll/optionupdate/",c,function(d){if(a(b).attr("o_id")==0){a(b).attr("o_id",d.o_id)}},"json")},delete_option:function(b){var c=a(b).parent().children("input").attr("o_id");if(c!=0){a.post("/poll/delete/",{oid:c},function(d){a.showmessage(" "+d.msg)},"json")}a(b).parent().empty()},question_added:function(b,c){a(b).attr("q_id",c);if(a.inArray(c,this.options.q_ids==-1)){this.options.q_ids.push(c);a("#q_ids").val(this.options.q_ids.toString())}},question_update:function(c){var b=this;if(a(c).val()!=""&&a(c).attr("originalval")!=a(c).val()){var d={poll_id:a("#poll_id").val(),option:a("#question_option").fieldSerialize(),name:a("#name").val(),key:a(b.options.permalink_sel).val(),question:a("#question").val(),q_id:a(c).attr("q_id"),};a.post("/poll/postquestion/",d,function(e){a.showmessage("Data Saved: "+e.poll.id);if(e.poll.id>0&&a("#poll_id").val()==0){a("#poll_id").val(e.poll.id);b.options.id=e.poll.id;b.question_added(c,e.poll.q_id)}},"json")}}});a.fn.cmsadmin=function(b){return this.each(function(){if(!a(this).is(".ds-cmsadmin")){new a.ds.cmsadmin(this,b)}})};a.ds.cmsadmin=function(d,e){var c={currentfolder:null,};e=e||{};a.extend(c,e);this.element=d;var b=this;b.options=c;a.data(this.element,"ds-cmsadmin",this);a("a.folderlink,a.folder.empty").click(function(){a(".activefolder").removeClass("activefolder");a(this).parent().addClass("activefolder");b.folderview(this)});a("span.file").click(function(){b.edit(this)})};a.extend(a.ds.cmsadmin.prototype,{edit:function(c){var b=this;var d=a(c).attr("objid");a(".activefolder").removeClass("activefolder");a(c).addClass("activefolder");a.get("/cms/edit/"+d,function(e){a("#CmsItemFormWrapper").html(e);b.formsetup()})},formsetup:function(){a("#cmsform").submit(function(){var c=a("#item_type").val();var g=a("#title").val();var h=a("#objectid").val();var f=a("#parentid").val();var b=0;a(this).ajaxSubmit({success:function(i,j){if(j=="success"){b=i;a.showmessage("Item Updated  "+b)}else{a.showmessage("There was an error  ")}}});var d="";var e="";a("body").attr("fake",b);if(c=="folder"&&h==0){d='<li><span class="folder empty"  id="item'+b+'" objid="'+b+'"><a href="javascript:void(0);" objid="'+b+'" class="folderlink" src="">'+g+'</a></span><ul id="cmsitem_'+b+'"></ul></li>';e=a(d).appendTo("#cmsitem_"+f)}else{if(c=="cms"&&h==0){d='<li class="last"><span id="item'+b+'" class="file" objid="'+b+'">'+g+"</span></li>";alert(d);a("#list"+f).children().removeClass("last");e=a(d).appendTo("#list"+f)}else{if(h>0){a("#item"+h).html(g)}else{}}}if(h==0){a("#ContentContextTree").treeview({add:e})}return false})},folderview:function(c){var b=this;var d=a(c).attr("objid");a.get("/cms/viewfolder/"+d,function(e){a("#CmsItemFormWrapper").html(e).attr("objid",d);a("#addcontentitem").click(function(){b.cmsadd(this)});a("#addfolder").click(function(){b.addfolder()});a("#editfolder").click(function(){b.editfolder(a("#editfolder"))});a("#sorttab").click(b.sorttab);a("#nodechildrenlist").sortable({stop:b.sortcomplete})})},sorttab:function(){a("div.boxlinks a").removeClass("current");a("#sorttab").addClass("current")},sortcomplete:function(c,d){var b="";a("#nodechildrenlist > li").each(function(){b+=a(this).attr("objid")+","});var e=a("#nodechildrenlist").attr("objid");a.ajax({type:"POST",url:"/cms/reorder/"+e,data:"ids="+b,success:function(f){a.showmessage("Data Saved: "+f)}})},addfolder:function(){var b=this;a("div.boxlinks a").removeClass("current");a("#addfolder").addClass("current");var c=a("#CmsItemFormWrapper").attr("objid");if(c>0){a.get("/cms/addfolder/"+c,function(d){a("#cmsformtarget").html(d);b.formsetup();a("#title").focus();a("#parentid").val(c)})}else{alert("whoops, no parentid")}},cmsadd:function(c){var b=this;a("div.boxlinks a").removeClass("current");a("#addcontentitem").addClass("current");var d=a(c).attr("objid");if(d>0){a.get("/cms/additem/",function(e){a("#cmsformtarget").html(e);a("#title").focus();a("#parentid").val(d);b.formsetup()})}},editfolder:function(c){var b=this;a("div.boxlinks a").removeClass("current");a("#editfolder").addClass("current");var d=a(c).attr("objid");if(d>0){a.get("/cms/edit/"+d,function(e){a("#cmsformtarget").html(e);b.formsetup()})}}});a.ds.humanMsg={msgId:"humanMsg",msgOpacity:0.8,tmin:1500,tmax:5000,t2:5000,t1:700,removeMsg:null,setup:function(b,c){this.msgID="humanMsg";if(b==undefined){b="body"}this.msgOpacity=0.8;if(c!=undefined){this.msgOpacity=parseFloat(c)}jQuery(b).append('<div id="'+this.msgID+'" class="humanMsg"><div class="round"></div><p></p><div class="round"></div></div>')},displayMsg:function(b){if(b==""){return}clearTimeout(this.t2);jQuery("#"+this.msgID+" p").html(b);jQuery("#"+this.msgID+"").show().animate({opacity:this.msgOpacity});this.t1=setTimeout("$.ds.humanMsg.bindEvents()",this.tmin);this.t2=setTimeout("$.ds.humanMsg.removeMsg()",this.tmax)},bindEvents:function(){jQuery(window).mousemove(this.removeMsg).click(this.removeMsg).keypress(this.removeMsg)},removeMsg:function(){var b=a.ds.humanMsg;jQuery(window).unbind("mousemove",b.removeMsg).unbind("click",b.removeMsg).unbind("keypress",b.removeMsg);if(jQuery("#"+b.msgID).css("opacity")==b.msgOpacity){jQuery("#"+b.msgID).animate({opacity:0},500,function(){jQuery(this).hide()})}}}})(jQuery);jQuery(document).ready(function(){$.ds.humanMsg.setup()});(function(a){a.ds=a.ds||{};a.extend(a.ds,{parseUri:function(f){if(f==undefined){f=window.location.href}var e={strictMode:false,key:["source","protocol","authority","userInfo","user","password","host","port","relative","path","directory","file","query","anchor"],q:{name:"queryKey",parser:/(?:^|&)([^&=]*)=?([^&]*)/g},parser:{strict:/^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*):?([^:@]*))?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,loose:/^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*):?([^:@]*))?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/}};var b=e.parser[e.strictMode?"strict":"loose"].exec(f),d={},c=14;while(c--){d[e.key[c]]=b[c]||""}d[e.q.name]={};d[e.key[12]].replace(e.q.parser,function(h,g,i){if(g){d[e.q.name][g]=i}});return d},defaults:{logon_form_loaded:false,logon_form_selector:"#ds-logonform-div",logon_form_cancel:"#ds-showinputform-link",logon_form_link:"#ds-logon-link",input_form_selector:"#ds-inputform-div",current_url:"",use_sub_domains:false,base_url:"http://localhost:4950",site_slug:"enter your site id here"},prepLogon:function(c){a(c).append('<div id="ds-logonform-div" style="display:none;"></div>                 <a href="javascript:void(0);" id="ds-logon-link" >Show Logon</a>                 <a href="javascript:void(0);" id="ds-showinputform-link" style="display:none;">Cancel</a>');var b=this;var d=this.defaults;a(d.logon_form_link).click(function(){b.showLogon()});a(d.logon_form_cancel).click(function(){b.hideLogon()})},showLogon:function(){var c=this;var d=this.defaults;if(d.logon_form_loaded==true){}else{d.logon_form_loaded=true;var b="url="+encodeURIComponent(window.location.href);a(d.logon_form_selector).html('<iframe width="100%" height="150" frameborder="0"                     src="'+d.base_url+"/comment/login?"+b+'" allowtransparency="true"                     vspace="0" hspace="0" marginheight="0" marginwidth="0" id="ds-input-loginform" ></iframe>')}a(d.input_form_selector+","+d.logon_form_link).hide();a(d.logon_form_selector+","+d.logon_form_cancel).show()},hideLogon:function(){var b=this;var c=this.defaults;a(c.input_form_selector+","+c.logon_form_link).show();a(c.logon_form_selector+","+c.logon_form_cancel).hide()},service_url:function(d,e){var b=a.ds.parseUri(window.location.href);var c=this.defaults.base_url+d+"/"+encodeURIComponent(this.defaults.site_slug)+"?";c+=a.param({ref_url:(b.protocol+"://"+b.authority+b.relative),site_slug:this.defaults.site_slug});return c},dsactivity:function(f){var g=a.extend({use_url:false,activity:null,absolute:false,unique_id:null,category:null,custom:null},f);var e="";var b=a.ds.parseUri(window.location.href);var h={};var d=this.service_url("/apipublic/activity",true);if(g.use_url==true){if(g.absolute==true){g.activity=b.protocol+"://"+b.authority}g.activity+=b.relative}d+="&activity="+encodeURIComponent(g.activity);h=a.extend(h,{activity:g.activity});if(g.unique_id!=null){h=a.extend(h,{unique_id:g.unique_id})}if(g.category!=null){h=a.extend(h,{category:g.category})}if(g.custom!=null){var i="";for(var c in g.custom){i+=c+",";h[c]=g.custom[c]}h=a.extend(h,{cnames:i})}if(g.activity!=null){a.getJSON(d+"&jsoncallback=?",a.param(h),function(j){alert("success or failure?"+j)})}}});a.fn.dsactivity=function(b){var d={};var c=a.extend(d,b);this.each(function(){var e=a(this);e.click(function(){if(e.attr("activity")){c.activity=e.attr("activity");a.ds.dsactivity(c)}else{c.activity=this.textContent;a.ds.dsactivity(c)}});e.submit(function(){alert("in submit of form activity")})})};a.fn.dspoll=function(b){return this.each(function(){if(!a(this).is("ds-dspoll")){new a.ds.dspoll(this,b)}})};a.ds.dspoll=function(d,c){var e=a.extend({view_selector:".ds-poll-results-target",poll_id:0,getremote:""},a.ds.defaults,c);this.element=d;var b=this;this.poll_id=a("#poll_id",a(b.element)).val();this.q_id=a("#q_id",a(b.element)).val();b.options=e;a.data(this.element,"ds-dspoll",this);if(e.getremote!==""){b.display(d,e.getremote)}a("div.ds-poll-vote a",a(b.element)).click(function(){b.show_results()});a("div.ds-poll-vote input",a(b.element)).click(function(){b.vote(this)});return this};a.extend(a.ds.dspoll.prototype,{show_results:function(c){var b=this;a("div.ds-poll-vote,.ds-poll-question",a(b.element)).hide();a(this.options.view_selector,a(b.element)).children().show();return this},vote:function(d){var b=this;var e=a(".ds-poll-question div input[@checked]",a(b.element)).val();var f={poll_id:b.poll_id,q_id:this.q_id,options:e};var c=b.options.base_url+"/pollpublic/vote";a.getJSON(c+"?jsoncallback=?",f,function(g){a(b.element).hide();a(b.element).after(g.html);a("#"+g.htmlid).show();a.ds.dsactivity({activity:"User Voted On"+g.key,category:"Poll"})})},display:function(d,e){var b=this;var c=this.options.base_url+"/pollpublic/display/"+e;a.getJSON(c+"?jsoncallback=?",{},function(f){a(d).append(f.html);if(b.options.success){b.options.success()}if(a.browser.safari){a("style",a(d)).each(function(){a("head").append('<style id="injectedCss" type="text/css">'+a(this).text()+"</style>");a(this).text("")})}})}});a.fn.dshints=function(c,b){var d=a.extend({hint_selector:".hint",hint_class:"hint"},b);a(d.hint_selector,this).each(function(){a(this).attr("hint",a(this).val())});a(d.hint_selector,this).focus(function(){if(a(this).hasClass(d.hint_class)&&(a(this).val()==a(this).attr("hint"))){a(this).val("");a(this).removeClass(d.hint_class)}});a(d.hint_selector,this).blur(function(){if(a(this).val()==""){a(this).val(a(this).attr("hint")).addClass(d.hint_class)}});a(this).submit(function(){a(d.hint_selector,this).each(function(){if(a(this).val()==a(this).attr("hint")){a(this).val("")}})})};a.fn.comments=function(b){return this.each(function(){if(!a(this).is(".ds-comments")){new a.ds.comments(this,b)}})};a.ds.comments=function(d,e){var c={commentiframe:true};a.ds.defaults.current_url=window.location.href;e=e||{};a.extend(c,a.ds.defaults,e);this.element=d;var b=this;a.data(this.element,"ds-comments",this);b.options=c;a.ds.prepLogon(this.element);if(e.commentiframe===false){a(a.ds.defaults.logon_form_link).click(function(){a.ds.showLogon();a("#ds-commentform-div",a(b.element)).hide()});a(a.ds.defaults.logon_form_cancel).click(function(){a("#ds-commentform-div",a(b.element)).show()});a("#commentform").submit(function(){var f=a(this).formSerialize();var g=a.ds.defaults.base_url+"/comment/commentsubmitjsonp/${c.site.slug}?jsoncallback=?&"+f;a.getJSON(g,{},function(h){a("#ds-commentform-div").html(h.html)});return false})}};a.fn.dsgroupac=function(b){};a.fn.dshelp=function(b){b=a.ds.faceboxmanager.prepare_help_facebox(b);return this.each(function(){if(!a(this).is(".ds-help")){new a.ds.help(this,b)}})};a.ds.faceboxmanager={defaults:{style:"facebox",rating:false,feedback:true,draggable:true,topinfo:false,resizable:true,script:false,content:{},use_current_url:false,source_url:"",url:"",help_url:"/api/json/help/root/help",help_popup_url:"/help/submitfeedback",faceboxprecontent:"#facebox_precontent_holder",faceboxcontent:"#facebox_content_holder",faceboxcontent2:"#facebox_content_holder2",isshown:false,isinitialized:false},groupac:function(){jQuery.facebox(this.get_groupac());a("#facebox .content").before('<div id="facebox_precontent_holder"></div>');a("#facebox").css({left:((window.innerWidth-670)/2),width:670,height:500});a("#facebox_precontent_holder").css({width:630})},load:function(c,b){if(c in this.defaults.content){alert("already here"+b)}else{this.defaults.content[c]=b}},get_groupac:function(){var c=this;var b="site_key&"+a.ds.defaults.site_slug;b+="&url="+c.defaults.url;return'<div id="ds-inputform-div"><iframe width="100%" height="420" width="570" frameborder="0"             src="'+a.ds.defaults.base_url+"/groupadmin/popup/"+a.ds.defaults.site_slug+"?"+b+'"              allowtransparency="true" vspace="0" hspace="0" marginheight="0" marginwidth="0"             name="ds-input-form"></iframe></div>'},prepare_help_facebox:function(c){var d=a.extend({},this.defaults,c);var b=this;b.options=d;if(d.use_current_url==true){d.script=true,result=a.ds.parseUri(window.location.href);d.url=a.ds.defaults.base_url+d.help_url+result.relative.replace("#","");d.source_url=result.relative}return d}};a.ds.help=function(e,d){var f=a.extend({isloaded:false,hotkeys:false,showtitle:false},a.ds.faceboxmanager.defaults,d);this.element=e;var c=this;c.options=f;var b=(f.style==="facebox");if((f.style==="facebox")){a(e).click(function(){c.load_content();return false});if(f.hotkeys===true){if(typeof(a.hotkeys)!="undefined"){a.hotkeys.add("Shift+?",{disableInInput:true,type:"keypress"},function(){if(a.facebox.settings.isshown==false){c.load_content()}else{a.facebox.settings.isshown=false;a("#facebox .close").trigger("click")}})}}}else{if(f.style=="popup"){a(e).click(function(){var g=a.ds.parseUri(window.location.href);var h=a.ds.defaults.base_url+f.help_popup_url+"/"+encodeURIComponent(a.ds.defaults.site_slug)+"?";h+=a.param({ref_url:(g.protocol+"://"+g.authority+g.relative),site_slug:a.ds.defaults.site_slug});window.open(h,"mywindow","location=1,status=1,scrollbars=1,width=500,height=400")})}}return this};a.extend(a.ds.help.prototype,{load_content:function(){var b=this;a.facebox.loading();if(b.options.isloaded===false&&b.options.topinfo){a.getJSON(b.options.url+"?jsoncallback=?",{},function(e){b.topcontent=e.html;b.options.isloaded=true;a(b.options.faceboxprecontent).append(b.topcontent)})}jQuery.facebox("");if(typeof a.fn.draggable!="undefined"){a("#facebox").draggable()}a(document).bind("close.facebox",function(){b.on_close();a("#facebox_precontent_holder").remove();a("#facebox_content_holder2").remove();a("#facebook_esc_close").remove()});a("#facebox .content").before('<div id="facebox_precontent_holder"></div>');a("#facebox .content").after('<div id="facebox_content_holder2"></div>');a("#facebox .footer").prepend('<span id="facebook_esc_close" class="" style="float:left;text-align:left;">ESC = Close this panel</span>');if(b.options.isloaded===false){b.options.isloaded=true}a("#facebox").css({left:((window.innerWidth-670)/2),width:670});a("#facebox_precontent_holder").css({width:630});if(b.options.topinfo){a(b.options.faceboxprecontent).append(b.topinfo())}if(b.options.rating){a(b.options.faceboxcontent2).append(b.rating());var d=false;a(".rating input",a(b.options.faceboxcontent2)).click(function(){if(d===false){b.rate(this)}})}a("img",a("#facebox")).each(function(){result=a.ds.parseUri(this.src);url=a.ds.defaults.base_url+result.relative;this.src=url});var c="help";if(b.options.showtitle){c=a(this.element).attr("category");a(b.options.faceboxprecontent).append("<h3>"+a(this.element).html()+"</h3>")}if(b.options.feedback){a(b.options.faceboxcontent2).append(b.feedback(c))}a.ds.prepLogon(a("#facebox_content_holder2"))},on_close:function(b){},rate:function(e){var b=this;var d=a("#ds-cms-collection").attr("rid");var f=(a(e).val()==="Yes")?"1":"-1";a(e).parent().parent().hide();var c=a.ds.service_url("/help/ratearticle",true);a.getJSON(c+"&jsoncallback=?",{resource_id:d,rating:f},function(g){a.ds.dsactivity({activity:"User submitted a rating on help",category:"Help"})})},topinfo:function(){return'<div class="help-header" style="float:right;">                 <img style="vertical-align: top;" src="http://www.demisauce.com/images/icon_help.png" alt="Help" />             </div>'},rating:function(){return'<div class="rating" style="text-align:right;margin:10px 0 0 0;">                 <h4>Was This Information Helpful?</h4>                 <form>                        <input id="helpful_yes" class="buttonx" type="button"  value="Yes" name="helpful"/>                         <input id="helpful_no" class="buttonx" type="button"  value="No" name="helpful"/>                 </form></div>'},feedback:function(d){var c=this;var b="site_key="+a.ds.defaults.site_slug;b+="&url="+c.options.url+"&category="+d;return'<div id="ds-inputform-div" ttestatt="fake" style="width:630;"><iframe width="100%" height="200" frameborder="0"             src="'+a.ds.defaults.base_url+"/help/feedback/"+a.ds.defaults.site_slug+"?"+b+'"              allowtransparency="true" vspace="0" hspace="0" marginheight="0" marginwidth="0"             name="ds-input-form"></iframe></div>'},xxxhideHelp:function(){var b=this;b.options.isshown=false;a(b.options.helpselector).hide()},xxxxshowHelp:function(){var b=this;a(b.options.helpselector).show();a.hotkeys.add("Esc",{disableInInput:true},function(){b.hideHelp()});a("a.close_help,a.demisauce-close-help").click(function(){b.hideHelp()});b.options.isshown=true}});a.fn.dstags=function(b){return this.each(function(){if(!a(this).is(".ds-tag-helper")){new a.ds.tag_helper(this,b)}})};a.ds.tag={defaults:{tag_div_selector:"#tag_list_div",tagged_class:"tagged_wdelete",tag_input:"#tags",id:"tbd"}};a.ds.tag_helper=function(f,d){var b=this;d=a.extend({tags:[],tagd:{}},a.ds.tag.defaults,d);b.first_tag=true;b.element=f;b.options=d;a.data(this.element,".ds-tag-helper",this);var c=d.tags;for(var e=0;e<c.length;e++){b.add_tag(c[e])}var b=this;a("a",a(f)).click(function(){b.click_tag(a(this).html())})};a.extend(a.ds.tag_helper.prototype,{add_tag:function(b){var c=this;if(c.first_tag===true){a(c.options.tag_input).focus();c.first_tag=false}if(b.indexOf(":")>0){a("#tag_"+b.replace(":","")).addClass(c.options.tagged_class)}else{a("#tag_"+b).addClass(c.options.tagged_class)}if(!(b in c.options.tagd)){c.options.tagd[b]=b;c.options.tags[c.options.length]=b}var d=",";var e=a(c.options.tag_input).val();if(e==""){d=""}a(c.options.tag_input).val(e+d+b)},click_tag:function(b){var c=this;if(!(b in c.options.tagd)){c.add_tag(b)}else{delete c.options.tagd[b];var e=[];for(var d in c.options.tagd){e[e.length]=d}c.options.tags=e;if(b.indexOf(":")>0){a("#tag_"+b.replace(":","")).removeClass(c.options.tagged_class)}else{a("#tag_"+b).removeClass(c.options.tagged_class)}a(c.options.tag_input).val(e.join(","))}}})})(jQuery);(function(a){a.ds=a.ds||{};a.fn.slugeditor=function(b){return this.each(function(){if(!a(this).is(".ds-slugeditor")){new a.ds.slugeditor(this,b)}})};a.ds.slugeditor=function(d,e){var c={permalink_sel:"#real_permalink",permalink_span:"#editable-slug-span",permalink_edit:"#editable-slug-href",permalink_div:"#permalink_div",slugfrom:"#title",strip:false};e=e||{};a.extend(c,e);this.element=d;var b=this;b.options=c;a.data(this.element,"ds-slugeditor",this);a(c.slugfrom).blur(function(f){b.show(this)});a(c.permalink_span+","+c.permalink_edit).click(function(){b.slugedit(this)})};a.extend(a.ds.slugeditor.prototype,{slugblur:function(c){var b=this;a(b.options.permalink_sel).hide();a(b.options.permalink_span).html(a(b.options.permalink_sel).val())},show:function(d){var c=this;a(c.options.permalink_sel).hide();a(c.options.permalink_span).html(a(c.options.permalink_sel).val());var b=a(c.options.permalink_sel).val();if(b==""){if(c.options.strip==true){b=a(c.options.slugfrom).val().replace(/ /g,"").toLowerCase().replace(/[^a-z\-]/g,"")}else{b=a(c.options.slugfrom).val().replace(/ /g,"-").toLowerCase().replace(/[^a-z\-]/g,"")}b=b.replace(/(-{2,50})/g,"-");a(c.options.permalink_sel).val(b)}else{}a(c.options.permalink_span).html(b)},slugedit:function(c){var b=this;b.show();a(b.options.permalink_sel).show().focus();a(b.options.permalink_sel).keypress(function(f){var d=f.charCode?f.charCode:f.keyCode?f.keyCode:0;if((13==d)||(27==d)){b.slugblur();return false}});a(b.options.permalink_sel).blur(function(d){a(this).hide();a(b.options.permalink_span).html(a(this).val())})}})})(jQuery);// Copyright 2007, Google Inc.
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
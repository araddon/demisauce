(function(a){a.extend(a.fn,{swapClass:function(c,b){return this.each(function(){var d=a(this);if(a.className.has(this,c)){d.removeClass(c).addClass(b)}else{if(a.className.has(this,b)){d.removeClass(b).addClass(c)}}})}});a(document).ready(function(){a(".demisauce_help_tip").tooltip({track:true,delay:0,showURL:false,showBody:" - ",opacity:0.9,width:260});a("form").dshints()});a.extend(a,{showmessage:function(b){a.ds.humanMsg.displayMsg(b)}});a.ds=a.ds||{};a.fn.emailadmin=function(b){return this.each(function(){if(!a(this).is(".ds-emailadmin")){new a.ds.emailadmin(this,b)}})};a.ds.emailadmin=function(d,e){var c={currentfolder:null,};e=e||{};a.extend(c,e);this.element=d;var b=this;b.options=c;a("a.cmsedit").click(function(){b.edit(this)});a.data(this.element,"ds-emailadmin",this)};a.extend(a.ds.emailadmin.prototype,{edit:function(b){var c=a(b).attr("objid");alert(" in email edit");if(c>0){a.get("/email/edit/"+c,function(d){a("#EmailItemFormWrapper").html(d)})}}});a.fn.ds_tabs=function(b){return this.each(function(){if(!a(this).is(".ds-tab")){new a.ds.tab(this,b)}})};a.ds.tab=function(c,b){a("a",a(c)).click(function(){a(this).parent().children(".current").each(function(d){currentTab=this.hash});a(this).parent().children().each(function(d){a(this).removeClass("current")});a(currentTab).hide();a(this.hash).show();a(this).addClass("current")})};a.fn.ds_poll_admin=function(b){return this.each(function(){if(!a(this).is(".ds-poll-admin")){new a.ds.polladmin(this,b)}})};a.ds.polladmin=function(d,c){var b=this;b.options=a.extend({isloaded:false,q_ids:[],id:0,permalink_sel:"#real_permalink",qoption_html:'<div><label for="option"></label>                             <img src="/images/move.png" border="0" style="border:0"/>                             <input id="question_option" class="tempforjq" o_id="0" name="question_option" style="width:350px" type="text" value="" />                             <img src="/images/cross.png" border="0" style="border:0" class="delete"/></div> ',},c);this.element=d;a("#name").focus();b.options.q_ids=a("#q_ids").val().split(",");a("#question_options div").sortable({items:"div",stop:b.option_sort_complete});a("#question_options div div input[o_id=0]").blur(function(){if(a(this).val()!=""){b.add_option(this)}else{b.remove_option(this)}});a("#question_options div div[type=other] input").each(function(){a(this).attr("disabled","disabled").next("img.delete").attr("src","")});a("#name,#question").each(function(){a(this).attr("originalval",a(this).val())});a("#question_options div div input").blur(function(){if(a(this).attr("originalval")!=a(this).val()){b.option_update(this);a(this).attr("originalval",a(this).val())}}).not("input[o_id=0]").each(function(){a(this).attr("originalval",a(this).val())});a("img.delete").not("input[o_id=0]").click(function(){b.delete_option(this)});a("#question").blur(function(){b.question_update(this)});a("form input[name=question_type]").click(function(){if(a(this).val()=="radiowother"){b.add_option(a("#question_options div div input:last"),"other")}else{if(a(this).val()=="radio"){a("#question_options div div[type=other]").empty()}else{if(a(this).val()=="multiplechoice"){a("#question_options div div[type=other]").empty()}}}});a("#jq_add_question").click(function(){a("#placeholder_for_newq").before(b.options.qoption_html)})};a.extend(a.ds.polladmin.prototype,{add_option:function(d,b){var c=this;if(b==undefined){a(d).parent().parent().append(c.options.qoption_html)}else{a(d).parent().after(c.options.qoption_html);a("#question_options div div input.tempforjq:first").val("other").attr("disabled","disabled").parent().attr("type","other")}a("#question_options div").sortable({items:"div",stop:c.option_sort_complete});a("#question_options div div input.tempforjq").blur(function(){c.add_option(this)}).removeClass("tempforjq").next().click(function(){c.delete_option(this)});a(d,"~ input").focus()},remove_option:function(b){a(b,"~ input").parent().empty();a("#question_options div div:last").empty()},option_sort_complete:function(c,e){var b=Array();a("#question_options div div input").each(function(){b.push("o_id="+a(this).attr("o_id"))});var f=a("#question_options div div input,#poll_id,#question_options div div input").fieldSerialize();f+="&"+b.join("&")+"&q_id="+a(this).parent().attr("q_id");a.post("/poll/sort/",f,function(d){a.showmessage("sort completed: ")},"json")},option_update:function(b){var c={poll_id:a("#poll_id").val(),question_option:a(b).val(),o_id:a(b).attr("o_id"),q_id:a(b).parent().parent().attr("q_id"),};a.post("/poll/optionupdate/",c,function(d){if(a(b).attr("o_id")==0){a(b).attr("o_id",d.o_id)}},"json")},delete_option:function(b){var c=a(b).parent().children("input").attr("o_id");if(c!=0){a.post("/poll/delete/",{oid:c},function(d){a.showmessage(" "+d.msg)},"json")}a(b).parent().empty()},question_added:function(b,c){a(b).attr("q_id",c);if(a.inArray(c,this.options.q_ids==-1)){this.options.q_ids.push(c);a("#q_ids").val(this.options.q_ids.toString())}},question_update:function(c){var b=this;if(a(c).val()!=""&&a(c).attr("originalval")!=a(c).val()){var d={poll_id:a("#poll_id").val(),option:a("#question_option").fieldSerialize(),name:a("#name").val(),key:a(b.options.permalink_sel).val(),question:a("#question").val(),q_id:a(c).attr("q_id"),};a.post("/poll/postquestion/",d,function(e){a.showmessage("Data Saved: "+e.poll.id);if(e.poll.id>0&&a("#poll_id").val()==0){a("#poll_id").val(e.poll.id);b.options.id=e.poll.id;b.question_added(c,e.poll.q_id)}},"json")}}});a.fn.cmsadmin=function(b){return this.each(function(){if(!a(this).is(".ds-cmsadmin")){new a.ds.cmsadmin(this,b)}})};a.ds.cmsadmin=function(d,e){var c={currentfolder:null,};e=e||{};a.extend(c,e);this.element=d;var b=this;b.options=c;a.data(this.element,"ds-cmsadmin",this);a("a.folderlink,a.folder.empty").click(function(){a(".activefolder").removeClass("activefolder");a(this).parent().addClass("activefolder");b.folderview(this)});a("span.file").click(function(){b.edit(this)})};a.extend(a.ds.cmsadmin.prototype,{edit:function(c){var b=this;var d=a(c).attr("objid");a(".activefolder").removeClass("activefolder");a(c).addClass("activefolder");a.get("/cms/edit/"+d,function(e){a("#CmsItemFormWrapper").html(e);b.formsetup()})},formsetup:function(){a("#cmsform").submit(function(){var c=a("#item_type").val();var g=a("#title").val();var h=a("#objectid").val();var f=a("#parentid").val();var b=0;a(this).ajaxSubmit({success:function(i,j){if(j=="success"){b=i;a.showmessage("Item Updated  "+b)}else{a.showmessage("There was an error  ")}}});var d="";var e="";a("body").attr("fake",b);if(c=="folder"&&h==0){d='<li><span class="folder empty"  id="item'+b+'" objid="'+b+'"><a href="javascript:void(0);" objid="'+b+'" class="folderlink" src="">'+g+'</a></span><ul id="cmsitem_'+b+'"></ul></li>';e=a(d).appendTo("#cmsitem_"+f)}else{if(c=="cms"&&h==0){d='<li class="last"><span id="item'+b+'" class="file" objid="'+b+'">'+g+"</span></li>";alert(d);a("#list"+f).children().removeClass("last");e=a(d).appendTo("#list"+f)}else{if(h>0){a("#item"+h).html(g)}else{}}}if(h==0){a("#ContentContextTree").treeview({add:e})}return false})},folderview:function(c){var b=this;var d=a(c).attr("objid");a.get("/cms/viewfolder/"+d,function(e){a("#CmsItemFormWrapper").html(e).attr("objid",d);a("#addcontentitem").click(function(){b.cmsadd(this)});a("#addfolder").click(function(){b.addfolder()});a("#editfolder").click(function(){b.editfolder(a("#editfolder"))});a("#sorttab").click(b.sorttab);a("#nodechildrenlist").sortable({stop:b.sortcomplete})})},sorttab:function(){a("div.boxlinks a").removeClass("current");a("#sorttab").addClass("current")},sortcomplete:function(c,d){var b="";a("#nodechildrenlist > li").each(function(){b+=a(this).attr("objid")+","});var e=a("#nodechildrenlist").attr("objid");a.ajax({type:"POST",url:"/cms/reorder/"+e,data:"ids="+b,success:function(f){a.showmessage("Data Saved: "+f)}})},addfolder:function(){var b=this;a("div.boxlinks a").removeClass("current");a("#addfolder").addClass("current");var c=a("#CmsItemFormWrapper").attr("objid");if(c>0){a.get("/cms/addfolder/"+c,function(d){a("#cmsformtarget").html(d);b.formsetup();a("#title").focus();a("#parentid").val(c)})}else{alert("whoops, no parentid")}},cmsadd:function(c){var b=this;a("div.boxlinks a").removeClass("current");a("#addcontentitem").addClass("current");var d=a(c).attr("objid");if(d>0){a.get("/cms/additem/",function(e){a("#cmsformtarget").html(e);a("#title").focus();a("#parentid").val(d);b.formsetup()})}},editfolder:function(c){var b=this;a("div.boxlinks a").removeClass("current");a("#editfolder").addClass("current");var d=a(c).attr("objid");if(d>0){a.get("/cms/edit/"+d,function(e){a("#cmsformtarget").html(e);b.formsetup()})}}});a.ds.humanMsg={msgId:"humanMsg",msgOpacity:0.8,tmin:1500,tmax:5000,t2:5000,t1:700,removeMsg:null,setup:function(b,c){this.msgID="humanMsg";if(b==undefined){b="body"}this.msgOpacity=0.8;if(c!=undefined){this.msgOpacity=parseFloat(c)}jQuery(b).append('<div id="'+this.msgID+'" class="humanMsg"><div class="round"></div><p></p><div class="round"></div></div>')},displayMsg:function(b){if(b==""){return}clearTimeout(this.t2);jQuery("#"+this.msgID+" p").html(b);jQuery("#"+this.msgID+"").show().animate({opacity:this.msgOpacity});this.t1=setTimeout("$.ds.humanMsg.bindEvents()",this.tmin);this.t2=setTimeout("$.ds.humanMsg.removeMsg()",this.tmax)},bindEvents:function(){jQuery(window).mousemove(this.removeMsg).click(this.removeMsg).keypress(this.removeMsg)},removeMsg:function(){var b=a.ds.humanMsg;jQuery(window).unbind("mousemove",b.removeMsg).unbind("click",b.removeMsg).unbind("keypress",b.removeMsg);if(jQuery("#"+b.msgID).css("opacity")==b.msgOpacity){jQuery("#"+b.msgID).animate({opacity:0},500,function(){jQuery(this).hide()})}}}})(jQuery);jQuery(document).ready(function(){$.ds.humanMsg.setup()});
(function(a){a.ds=a.ds||{};a.fn.slugeditor=function(b){return this.each(function(){if(!a(this).is(".ds-slugeditor")){new a.ds.slugeditor(this,b)}})};a.ds.slugeditor=function(d,e){var c={permalink_sel:"#real_permalink",permalink_span:"#editable-slug-span",permalink_edit:"#editable-slug-href",permalink_div:"#permalink_div",slugfrom:"#title",strip:false};e=e||{};a.extend(c,e);this.element=d;var b=this;b.options=c;a.data(this.element,"ds-slugeditor",this);a(c.slugfrom).blur(function(f){b.show(this)});a(c.permalink_span+","+c.permalink_edit).click(function(){b.slugedit(this)})};a.extend(a.ds.slugeditor.prototype,{slugblur:function(c){var b=this;a(b.options.permalink_sel).hide();a(b.options.permalink_span).html(a(b.options.permalink_sel).val())},show:function(d){var c=this;a(c.options.permalink_sel).hide();a(c.options.permalink_span).html(a(c.options.permalink_sel).val());var b=a(c.options.permalink_sel).val();if(b==""){if(c.options.strip==true){b=a(c.options.slugfrom).val().replace(/ /g,"").toLowerCase().replace(/[^a-z\-]/g,"")}else{b=a(c.options.slugfrom).val().replace(/ /g,"-").toLowerCase().replace(/[^a-z\-]/g,"")}b=b.replace(/(-{2,50})/g,"-");a(c.options.permalink_sel).val(b)}else{}a(c.options.permalink_span).html(b)},slugedit:function(c){var b=this;b.show();a(b.options.permalink_sel).show().focus();a(b.options.permalink_sel).keypress(function(f){var d=f.charCode?f.charCode:f.keyCode?f.keyCode:0;if((13==d)||(27==d)){b.slugblur();return false}});a(b.options.permalink_sel).blur(function(d){a(this).hide();a(b.options.permalink_span).html(a(this).val())})}})})(jQuery);
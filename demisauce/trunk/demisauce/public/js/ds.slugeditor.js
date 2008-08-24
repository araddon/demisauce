(function($){
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
})(jQuery);
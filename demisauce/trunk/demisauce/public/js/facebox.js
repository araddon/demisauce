/*
 * Facebox w Modifications for Demisauce
 * Based off of Facebox version: 1.2 (05/05/2008)
 * @requires jQuery v1.2 or later and Jquery Draggable
 *
 * Examples at http://famspam.com/facebox/
 *
 * Licensed under the MIT:
 *   http://www.opensource.org/licenses/mit-license.php
 *
 * Copyright 2007, 2008 Chris Wanstrath [ chris@ozmm.org ]
 *
 * Usage:
 *  
 *  jQuery(document).ready(function() {
 *    jQuery('a[rel*=facebox]').facebox() 
 *  })
 *
 *  <a href="#terms" rel="facebox">Terms</a>
 *    Loads the #terms div in the box
 *
 *  <a href="terms.html" rel="facebox">Terms</a>
 *    Loads the terms.html page in the box
 *
 *  <a href="terms.png" rel="facebox">Terms</a>
 *    Loads the terms.png image in the box
 *
 *
 *  You can also use it programmatically:
 * 
 *    jQuery.facebox('some html')
 *
 *  The above will open a facebox with "some html" as the content.
 *    
 *    jQuery.facebox(function($) { 
 *      $.get('blah.html', function(data) { $.facebox(data) })
 *    })
 *
 *  The above will show a loading screen before the passed function is called,
 *  allowing for a better ajaxy experience.
 *
 *  The facebox function can also display an ajax page or image:
 *  
 *    jQuery.facebox({ ajax: 'remote.html' })
 *    jQuery.facebox({ image: 'dude.jpg' })
 *    jQuery.facebox({ script: 'http://www.example.com/script/script.js'})
 *
 *  Want to close the facebox?  Trigger the 'close.facebox' document event:
 *
 *    jQuery(document).trigger('close.facebox')
 *
 *  Facebox also has a bunch of other hooks:
 *
 *    loading.facebox
 *    beforeReveal.facebox
 *    reveal.facebox (aliased as 'afterReveal.facebox')
 *    init.facebox
 *
 *  Simply bind a function to any of these hooks:
 *
 *   $(document).bind('reveal.facebox', function() { ...stuff to do after the facebox and contents are revealed... })
 *
 */
(function($) {
    $.facebox = function(data, klass) {
        $.facebox.loading()

        if (data.ajax) fillFaceboxFromAjax(data.ajax)
        else if (data.image) fillFaceboxFromImage(data.image)
        else if (data.div) fillFaceboxFromHref(data.div)
        else if ($.isFunction(data)) data.call($)
        else $.facebox.reveal(data, klass)
    }

    /*
    * Public, $.facebox methods
    */
   $.extend($.facebox, {
        settings: {
            opacity      : .20,
            overlay      : true,
            isshown      : false,
            width        : 630,
            min_height   : 300,
            content_selector     : '#facebox-content-section',
            base_url     : 'http://localhost:4950',
            loadingImage : '/images/facebox/loading.gif',
            closeImage   : '/images/facebox/closelabel.gif',
            helpImage   : '/images/facebox/closelabel.gif',
            imageTypes   : [ 'png', 'jpg', 'jpeg', 'gif' ],
            faceboxHtml  : '\
            <div id="facebox" style="display:none;"> \
              <div class="popup"> \
                <table> \
                  <tbody> \
                    <tr> \
                      <td class="tl"/><td class="b"/><td class="tr"/> \
                    </tr> \
                    <tr> \
                      <td class="b"/> \
                      <td class="body"> \
                        <div id="facebox-content-section" style=""> \
                            <div id="facebox_precontent_holder"></div> \
                            <div id="facebox_content_holder" class="content"> \
                            </div> \
                            <div id="facebox_content_holder2"> \
                            </div> \
                        </div> \
                        <div class="footer"> \
                          <span class="" style="float:left;text-align:left;">ESC = Close this panel</span> \
                          <a href="#" class="close"> \
                            <img src="/images/facebox/closelabel.gif" title="close" class="close_image" /> \
                          </a> \
                        </div> \
                      </td> \
                      <td class="b"/> \
                    </tr> \
                    <tr> \
                      <td class="bl"/><td class="b"/><td class="br"/> \
                    </tr> \
                  </tbody> \
                </table> \
              </div> \
            </div>'
        },

        loading: function() {
            init()
            if ($('#facebox .loading').length == 1) return true;
            showOverlay();

            
            $('#facebox .body').children().hide().end().append(
              '<div class="loading"><img src="'+$.facebox.settings.loadingImage+'"/></div>')
            $('#facebox').css({
                top:	getPageScroll()[1] + (getPageHeight() / 10),
                left:	385.5,
                width: $.facebox.settings.width + 40
            }).show().draggable();
            $($.facebox.settings.content_selector).css({width: $.facebox.settings.width});

            $(document).bind('keydown.facebox', function(e) {
                // || e.keyCode == 32
                if (e.keyCode == 27) $.facebox.close();// 27=esc,32=space
                return true;
            })
            $(document).trigger('loading.facebox');
        },
        
        reveal: function(data, klass, source) {
            $(document).trigger('beforeReveal.facebox');
            if ($('#facebox .content').attr('src') != source || typeof source == 'undefined'){
                $('#facebox .content').empty();
                if (typeof source == 'undefined'){
                    if (typeof data.html == 'undefined'){
                        $('#facebox .content').append(data).attr('src',data);
                    }
                    //$('#facebox .content').append(data.html()).attr('src',source);
                } else {
                    $('#facebox .content').append(data).attr('src',source);
                }
            }
            if (klass) $('#facebox .content').addClass(klass);
            $('#facebox .loading').remove();
            //$('#facebox').show();
            $('#facebox .body').children().fadeIn('normal');
            $('#facebox').css('left', $(window).width() / 2 - ($('#facebox table').width() / 2));
            if($('#facebox').height() < this.settings.min_height){
                $('#facebox').height(this.settings.min_height);
            }
            $(document).trigger('reveal.facebox');
            $(document).trigger('afterReveal.facebox');
        },
        close: function() {
            $(document).trigger('close.facebox');
            $('#facebox_content_holder2').empty();
            $('#facebox_precontent_holder').empty();
            $.facebox.settings.isshown = false;
            return false;
        }
    })

    /*
    * Public, $.fn methods
    */
    $.fn.facebox = function(settings) {
        init(settings)
        var self = this;
        function clickHandler() {
            $.facebox.loading(true)
            // support for rel="facebox.inline_popup" syntax, to add a class
            // also supports deprecated "facebox[.inline_popup]" syntax
            var klass = this.rel.match(/facebox\[?\.(\w+)\]?/)
            if (klass) klass = klass[1]
            if (typeof settings.script != 'undefined'){
                fillFaceboxFromScriptInclude(settings.source_url, klass,self);
            } else if (typeof settings.ajax != 'undefined') {
                fillFaceboxFromajax(settings.ajax,klass);
            } else if (typeof settings.ajax == 'undefined'){
                fillFaceboxFromHref(this.href, klass)
            } else {
                fillFaceboxFromScriptInclude(settings.source_url, klass);
            }
            return false;
        }
        
        return this.click(clickHandler)
    }

    /*
    * Private methods
    */

    // called one time to setup facebox on this page
    function init(settings) {
        if ($.facebox.settings.inited) return true
        else $.facebox.settings.inited = true

        $(document).trigger('init.facebox')
        makeCompatible()

        var imageTypes = $.facebox.settings.imageTypes.join('|')
        $.facebox.settings.imageTypesRegexp = new RegExp('\.' + imageTypes + '$', 'i')

        if (settings) $.extend($.facebox.settings, settings)
        $('body').append($.facebox.settings.faceboxHtml)
        
        //$('#demisauce_help').click(function(){
        //    $(self).trigger('click')
        //});

        var preload = [ new Image(), new Image() ]
        preload[0].src = $.facebox.settings.base_url + $.facebox.settings.closeImage
        preload[1].src = $.facebox.settings.base_url + $.facebox.settings.loadingImage

        $('#facebox').find('.b:first, .bl, .br, .tl, .tr').each(function() {
          preload.push(new Image())
          preload.slice(-1).src = $(this).css('background-image').replace(/url\((.+)\)/, '$1')
        })

        $('#facebox .close').click($.facebox.close)
        $('#facebox .close_image').attr('src',$.facebox.settings.base_url +  $.facebox.settings.closeImage)
    }

    // getPageScroll() by quirksmode.com
    function getPageScroll() {
        var xScroll, yScroll;
        if (self.pageYOffset) {
            yScroll = self.pageYOffset;
            xScroll = self.pageXOffset;
        } else if (document.documentElement && document.documentElement.scrollTop) {	 // Explorer 6 Strict
            yScroll = document.documentElement.scrollTop;
            xScroll = document.documentElement.scrollLeft;
        } else if (document.body) {// all other Explorers
            yScroll = document.body.scrollTop;
            xScroll = document.body.scrollLeft;	
        }
        return new Array(xScroll,yScroll) 
    }

    // Adapted from getPageSize() by quirksmode.com
    function getPageHeight() {
        var windowHeight
        if (self.innerHeight) {	// all except Explorer
            windowHeight = self.innerHeight;
        } else if (document.documentElement && document.documentElement.clientHeight) { // Explorer 6 Strict Mode
            windowHeight = document.documentElement.clientHeight;
        } else if (document.body) { // other Explorers
            windowHeight = document.body.clientHeight;
        }	
        return windowHeight
    }

    // Backwards compatibility
    function makeCompatible() {
        var $s = $.facebox.settings

        $s.loadingImage = $s.loading_image || $s.loadingImage
        $s.closeImage = $s.close_image || $s.closeImage
        $s.imageTypes = $s.image_types || $s.imageTypes
        $s.faceboxHtml = $s.facebox_html || $s.faceboxHtml
    }

    // Figures out what you want to display and displays it
    // formats are:
    //     div: #id
    //   image: blah.extension
    //    ajax: anything else
    function fillFaceboxFromHref(href, klass) {
        if (href.match(/#/)) {
            var url    = window.location.href.split('#')[0];
            var target = href.replace(url,'');
            $.facebox.reveal($(target).clone().show(), klass);
            $('#facebox .content').attr('src',target);
        } else if (href.match($.facebox.settings.imageTypesRegexp)) {
            fillFaceboxFromImage(href, klass);
        } else { 
            fillFaceboxFromScriptInclude(href, klass);
        }
    }

    function fillFaceboxFromImage(href, klass) {
        var image = new Image()
        image.onload = function() {
            $.facebox.reveal('<div class="image"><img src="' + image.src + '" /></div>', klass)
        }
        image.src = href
    }

    function fillFaceboxFromAjax(href, klass) {
        if ($('#facebox .content').attr('src') == href){
            $.facebox.reveal(null, klass,href);
        }else {
            $.ajax({
                type: "GET",
                url: href,
                success: function(data){
                    $.facebox.reveal(data, klass,href);
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    $.facebox.reveal(textStatus, klass,textStatus);
                 }
            });
        }
    }
    
    function fillFaceboxFromScriptInclude(href, klass,self) {
        if ($('#facebox .content').attr('src') == href){
            $.facebox.reveal(null, klass,href);
            self.trigger('loaded_script');
        }else {
            $.getScript(href, function(){
                $.facebox.reveal(facebox_content, 'dshelp',href);
                self.trigger('loaded_script');
            });
        }
    }

    function skipOverlay() {
        return $.facebox.settings.overlay == false || $.facebox.settings.opacity === null;
    }

    function showOverlay() {
        if (skipOverlay()) return;
        
        if ($('facebox_overlay').length == 0) 
        $("body").append('<div id="facebox_overlay" class="facebox_hide"></div>')
        
        $('#facebox_overlay').hide().addClass("facebox_overlayBG").css(
            'opacity', $.facebox.settings.opacity).click(
                function() { $(document).trigger('close.facebox') }).fadeIn(200);
        return false;
    }

    function hideOverlay() {
        if (skipOverlay()) return;
        
        $('#facebox_overlay').fadeOut(200, function(){
            $("#facebox_overlay").removeClass("facebox_overlayBG")
            $("#facebox_overlay").addClass("facebox_hide") 
            $("#facebox_overlay").remove()
        })
        
        return false;
    }

    /*
    * Bindings
    */
    $(document).bind('close.facebox', function() {
        $(document).unbind('keydown.facebox');
        $('#facebox').fadeOut(function() {
            //$('#facebox .content').removeClass().addClass('content');
            hideOverlay();
            $('#facebox .loading').remove();
        })
    })

})(jQuery);

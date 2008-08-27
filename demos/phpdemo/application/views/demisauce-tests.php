<div id="doc2" class="yui-t6">
    <div id="bd">

        <div id="yui-main">
            <div class="yui-b" id="jq-testing">
                <script type="text/javascript" src="<?php echo $demisauce_base_url;?>/js/ds.slugeditor.js"></script>
                <link rel="stylesheet" href="<?php echo $demisauce_base_url;?>/js/accordion/demo.css" />
            	<style type="text/css">
            		.xerror, .error { display: none }
            	</style>
                <script>
                    test("Demisauce ds.base.js()", function() {
                        $.ds.defaults.site_slug = 'demisauce';
                        $.ds.defaults.base_url = 'http://localhost:4950';
                        equals( "http://localhost:4950", $.ds.defaults.base_url, "need base url" );
                        ok( $.ds, "$.ds" );
                    });
                    test("ds.slugeditor", function() {
                        $('#real_permalink').val('');
                        $('#testform').slugeditor({slugfrom: '#subject'});
                        $('#subject').val("aaron's  good&() * 8 stuff").focus().blur();
                        equals( $('#real_permalink').val(), 'aarons-good-stuff', "slugeditor target fields should have illegal characters replaced" );
                        ok( $('#real_permalink').css("display") == 'none', "slug edit text field should not be visible initially" );
                        $('#editable-slug-span').trigger('click');
                        ok( $('#real_permalink').css("display") == 'inline', "should be visible after click" );
                        $('#real_permalink').val('aarons-good-stuff2').blur();
                        equals( $('#real_permalink').val(), 'aarons-good-stuff2', "should be able to click editable link and change slug" );
                    });
                    test("ds.poll", function() {
                        stop();
                        jQuery('#polltry1').dspoll({getremote:'what-should-the-new-features-be',success:function(){
                            equals( 'What should the new features be?', jQuery('#polltry1 div.ds-poll-title').html(), "Poll Title should be populated from client side get" );
                            start();
                        }});
                        equals( 'What should the new features be?', jQuery('#polltry3 div.ds-poll-title').html(), "Poll Title should be populated from server side get" );
                        
                    });
                    test("djangodemo helloworld service", function() {
                        equals( "not", 'fake', "check to see if remotehtml get worked" );
                        equals( "not", 'fake', "check to ensure logged on" );
                        equals( "not", 'fake', "make sure you can post a comment" );
                        equals( "not", 'fake', "and that it updated remote app" );
                        equals( "not", 'fake', "check to ensure logged off, repeat tests" );
                    });
                    test("ds.comment service", function() {
                        
                        ok( $('#demisauce-comment').html().indexOf('your displayname') > 0, "see if we got content from comment html" );
                    });

                </script>
                	<h1>Demisauce Client Test Suite</h1>
                	<h2 id="banner"></h2>
                	<h2 id="userAgent"></h2>
                	<ol id="tests"></ol>
                <div id="main">
                    <div id="log"><div><strong>Log Output:  </strong></div></div>
                </div>
                <form id="testform">
                    <div class="required">
                        <label for="subject">Subject:</label>
                        <input id="subject" type="text" value="" name="subject"/>
                    </div>
                    <div id="permalink_div" class="required" style="display: block;">
                        <label for="slug">Permalink:</label>
                        <span id="permalink" class="secondary">
                            <span id="editable-slug-span" title="Click to edit this part of the permalink"/>
                            <a id="editable-slug-href" href="javascript:void(0)">Edit</a>
                        </span>
                        <input id="permalink" type="hidden" value="" size="100"/>
                        <br/>
                        <input id="real_permalink" type="text" style="displayxx: show;" value="" name="real_permalink"/>
                    </div>
                </form>
            </div>
        </div>
        <div class="yui-b sidebar">
            <div class="basic"  id="aaronslist">
                <a>Django Helloworld html content</a>
                <div id="djangophphello" class="ds-poll">
                    <div class="ds-poll-title">remote django helloworld</div>
                    <div id="ds-django-hellocontent">
                        MISSING
                    </div>
                </div>
                <a>Poll using javascript load</a>
                <div id="polltry1"></div>
                <a>Poll using server load</a>
                <div id="polltry3"><?php echo $ds_poll_xml->html;?></div>
                <a>remotehtml comment:</a>
                <div id="ds-comment" class="ds-poll">
                     <div class="ds-poll-title">remote html comment</div>
                     <div id="demisauce-comment">
                        <?php echo $ds_comment;?>
                     </div>
                 </div>
            </div>
            <script type="text/javascript" >
                jQuery('#aaronslist').accordion({ 
                    autoHeight: true 
                });
            </script>
        </div>
    </div>
</div>
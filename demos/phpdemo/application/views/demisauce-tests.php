<div id="doc2" class="yui-t6">
    <div id="bd">

        <div id="yui-main">
            <div class="yui-b" id="jq-testing">
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
                        test("ds.poll", function() {
                            stop();
                            jQuery('#polltry1').dspoll({getremote:'what-should-the-new-features-be',success:function(){
                                equals( 'What should the new features be?', jQuery('#polltry1 div.ds-poll-title').html(), "Poll Title should be populated from client side get" );
                                start();
                            }});
                            equals( 'What should the new features be?', jQuery('#polltry3 div.ds-poll-title').html(), "Poll Title should be populated from server side get" );
                            
                        });
                        test("ds.comment service", function() {
                            equals( "not", 'fake', "check to see if remotehtml get worked" );
                            equals( "not", 'fake', "check to ensure logged on" );
                            equals( "not", 'fake', "make sure you can post a comment" );
                            equals( "not", 'fake', "and that it updated remote app" );
                            equals( "not", 'fake', "check to ensure logged off, repeat tests" );
                        });
                        test("djangodemo service", function() {
                            equals( "not", 'fake', "djangodemoservice discovery and download" );
                            equals( "not", 'fake', "djangodemoservice should not be visible" );
                        });
                    </script>
                	<h1>Demisauce Client Test Suite</h1>
                	<h2 id="banner"></h2>
                	<h2 id="userAgent"></h2>
                	<ol id="tests"></ol>
                <div id="main">
                    <div id="log"><div><strong>Log Output:  </strong></div></div>
                </div>

            </div>
        </div>
        <div class="yui-b sidebar">
            
            <div id="polltry1"></div>
            <div id="polltry2"></div>
            <div id="polltry3"><?php echo $ds_poll_html;?></div>
            
        </div>
    </div>
</div>
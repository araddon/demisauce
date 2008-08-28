<div id="doc2" class="yui-t6">
    <div id="bd">

        <div id="yui-main">
            <div class="yui-b">
                 <?=$body_content?>
                 
                <?php 
                if (!is_null($body_xml)) {
                    foreach($body_xml as $item):
                ?>
                        <b><a href="<?php echo $path.$item->attributes()->rid;?>"><?php echo $item->title;?></a></b><br />
                        <p><?php echo $item->content;?></p>

                <?php 
                    endforeach;
                }
                ?>
                    
                    
                <?php echo demisauce_html('poll','what-should-the-new-features-be'); ?>
                

            </div>
        </div>
        <div class="yui-b sidebar">
            
            <div id="polltry2"></div>
            <script type="text/javascript">
            jQuery(document).ready(function() {
                jQuery('#polltry2').dspoll({getremote:'what-should-the-new-features-be'});
            });
            </script>
            
        </div>
    </div>
</div>
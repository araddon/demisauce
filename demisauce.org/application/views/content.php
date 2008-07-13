<div id="doc2" class="yui-t6">
    <div id="bd">

        <div id="yui-main">
            <div class="yui-b">
                 <?=$body_content?>
                <?php foreach($body_xml as $item):?>

                <b><a href="<?php echo $path.$item->attributes()->rid;?>"><?php echo $item->title;?></a></b><br />
                <p><?php echo $item->content;?></p>

                <?php endforeach;?>

            </div>
        </div>
        <div class="yui-b sidebar">

            <!--
            <style type="text/css" media="screen">
            .ds-poll {background-color:#EBF4FA;border-color:#116092;border-style:solid;border-width:1px;
              -moz-border-radius:3px;-webkit-border-radius:3px; padding:5px 4px 5px 8px;}
              .ds-poll div {padding:2px;}
            .ds-poll-title {font-size:120%;font-weight:600;}
            .ds-poll-vote input {background-color:#EBE9ED;border-color:#116092;color:#235C9D;
                -moz-border-radius:3px;-webkit-border-radius:3px;cursor:pointer;
                border-style:solid;border-width:1px;font-size:120%;
                line-height:1.6em;padding:4px 16px;text-decoration:none;}
            #ds-poll-form div label {width:130px;display:inline!important;float:none!important;
                margin:0pt 0pt 0px;padding:0px 0px;text-align:left;}
            </style>
            -->
            
            <div id="polltry2"></div>
            <script type="text/javascript">
            jQuery(document).ready(function() {
                jQuery('#polltry2').dspoll({getremote:'aarons-third-poll--when-is-this-coming-out'});
            });
            </script>
            
        </div>
    </div>
</div>
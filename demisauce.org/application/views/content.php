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

            <?php echo $ds_poll_html;?>

        </div>

    </div>
</div>
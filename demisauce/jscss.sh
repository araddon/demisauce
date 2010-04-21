#!/usr/bin/env bash
# 
#  chmod +x jscss.sh
#  usage:   $jscss.sh 
#
#  Script to compress and combine JS/CSS
# 
# ----------------------------------------------------------------------------
#  TODO
#   - accept directory as parameter?
# ----------------------------------------------------------------------------
basedir=`pwd`/demisauce/static/js
cssdir=`pwd`/demisauce/static/css
echo "js Basedir = $basedir"
echo "css Basedir = $cssdir"

echo "Combinning all static js into single lib-js.js"
#$basedir/jquery.treeview.min.js
rm $basedir/lib-js.js
cat $basedir/jquery.dimensions.js $basedir/ui.mouse.js  \
    $basedir/jquery.cookie.js $basedir/ui.draggable.js $basedir/ui.sortable.js \
    $basedir/jquery.form.js $basedir/jquery.hotkeys.js $basedir/jquery.tooltip.js $basedir/facebox.js \
    $basedir/jquery.bgiframe.min.js $basedir/jquery.autocomplete.js > $basedir/lib-js.js
java -jar ~/dev/yuicompressor-2.4.2.jar $basedir/lib-js.js -o $basedir/lib-js-min.js


echo "Combinning all demisauce js into single ds-js.js"
rm $basedir/ds-js.js
rm $basedir/ds-js-min.js
cat $basedir/ds.base.js $basedir/ds.adminbase.js  \
    $basedir/ds.slugeditor.js > $basedir/ds-js.js
java -jar ~/dev/yuicompressor-2.4.2.jar $basedir/ds-js.js -o $basedir/ds-js-min.js
#java -jar ~/dev/compiler.jar --js $basedir/ds.adminbase.js --js_output_file $basedir/ds.adminbase.min.js
#java -jar ~/dev/compiler.jar --js $basedir/ds.base.js --js_output_file $basedir/ds.base.min.js
#java -jar ~/dev/compiler.jar --js $basedir/ds.slugeditor.js --js_output_file $basedir/ds.slugeditor.min.js
#java -jar ~/dev/compiler.jar --js $basedir/ds-js.js --js_output_file $basedir/ds-js-min.js

echo "Combinning all demisauce js into single ds.client.js"
#$basedir/gears_init.js \
rm $basedir/ds.client.js
rm $basedir/ds.client.min.js
cat $basedir/ds.base.js \
    $basedir/jquery.uploadify-v2.1.0/jquery.uploadify.v2.1.0.min.js \
    $basedir/jquery.uploadify-v2.1.0/swfobject.js \
    $basedir/ds.slugeditor.js > $basedir/ds.client.js
java -jar ~/dev/yuicompressor-2.4.2.jar $basedir/ds.client.js -o $basedir/ds.client.min.js

# now css
echo "Combinning js into single all-css.css"
rm $cssdir/all-css.css
cat $cssdir/local.css $cssdir/ds.widgets.css $basedir/jquery.treeview.css \
   $basedir/jquery.autocomplete.css > $cssdir/all-css.css



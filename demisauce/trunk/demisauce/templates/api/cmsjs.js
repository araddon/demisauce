<%def name="view(cmsitem,show_details=False)">
    % if cmsitem:
    ds_help_output += ' <div id="cmsitem_${cmsitem.id}"><b>${cmsitem.title}</b> \
        <p> ${cmsitem.clean_content.replace('&amp;apos;',"\\'")} </p></div>'
    % else:

    % endif
</%def>


var ds_help_output = '<style type="text/css" media="screen"> \
</style>'
ds_help_output += ' <div id="ds-cms-collection" rid="${c.resource_id}">'
% if c.cmsitems and len(c.cmsitems) > 0:
    % for item in c.cmsitems:
        % if len(item.children) > 0 and item.item_type == "folder":
            % for associtem in item.children:
                ${view(associtem.item)}
            % endfor
        % else:
            ${view(item)}
        % endif
    % endfor
% else:
    ds_help_output += '<div>No Content</div>'
    % if c.user and c.user.isadmin:
        ds_help_output += '<a href="${'%s/cms/add/%s?returnurl=%s' % (c.demisauce_url, c.resource_id, h.current_url()) }">Add Item</a>' 
    % else:
        ds_help_output += ''
    % endif
% endif

% if c.topinfo:
    ds_help_output += '<div class="box box2" id="facebox-section3-div"> \
        <h2>Top ${len(c.topinfo)} Questions</h2><ol>'
    % for item in c.topinfo:
        ds_help_output += '<li><a href="#">${item.title}</a></li>'
    % endfor
    ds_help_output += '</ol></div>'
% endif
ds_help_output += '</div>'
var facebox_content = ds_help_output;
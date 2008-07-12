var ds_comments_output = '<style type="text/css" media="screen"> \
    .ds-comment-event {background-color: #E4F2FD;margin:8px;} \
    .ds-comment-odd {background-color: #ccc;margin:8px;} \
</style>'
% if c.items and len(c.items) > 0:
    ds_comments_output += '<div><h3>${len(c.items)} Comments</h3></div>'
    % for item in c.items:
        ds_comments_output += '<div class="${h.cycle("ds-comment-event", "ds-comment-odd") }">' 
        % if item.hashedemail:
            ds_comments_output += ' <img alt="" src="http://www.gravatar.com/avatar/${item.hashedemail}?s=24" class="avatar avatar-48" height="24" width="24">'
        % endif
        % if item.blog:
            ds_comments_output += '<a href="${item.blog}" >${item.authorname}</a>'
        % else:
            ds_comments_output += '${item.authorname}'
        %endif
        ds_comments_output += ' on ${item.created.strftime("%b %d, %Y")}<br /> ${item.clean_comment.replace('&amp;apos;',"\\'")}'
        
        ds_comments_output += '</div>'
        //${h.distance_of_time_in_words(item.created)}
    % endfor
    
% else:
    ds_comments_output += '<div>No Comments</div>'
    
% endif
ds_comments_output += '<div id="ds-inputform-div"><iframe width="100%" height="200" frameborder="0" \
    src="${h.base_url()}/comment/commentform/${c.site.slug}?url=${c.url}"  allowtransparency="true" \
    vspace="0" hspace="0" marginheight="0" marginwidth="0" name="ds-input-login"></iframe></div>\
    <form><input type="hidden" id="source_url" name="source_url" value="${c.url}" /></form>';


if(typeof($(document).ready) == 'undefined') {
    //alert('hmm, undefined');
}else{
    if(typeof($().comments) != 'undefined') {
        $('#demisauce-comments').append(ds_comments_output);
        $('#demisauce-comments').comments({'site_slug':"${c.site_slug}",'base_url':'${c.base_url}'});
    }
}

<%inherit file="_base.mako"/>
<%def name="title()">Demisauce Pylons Demo Site Blog Page</%def>
 

<%def name="topcontent()">
    <div id="callout">
	    <div id="calloutblock">
	        <h2>What's New?</h2>
	        <p>Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
            Nam iaculis adipiscing mi. Nulla vulputate mi at lorem. Fusce tincidunt
            dui non lectus euismod faucibus.</p>
	        <p><a href="#" title="link">Learn more&#8230;</a></p>
	    </div>
    </div>
</%def>


<%
#h.remote_html(routes_dict='key',append_path=True)
nodes = h.demisauce_xmlnodes(routes_dict='key',append_path=True,random=False)
%>
% if nodes:
    <div id="blog">
    % for node in nodes:
        <div>
            <h2>${node.title}</h2>
            <!--Note, this works as well:
                <h2>${node['title']} </h2> -->
            <p class="date">${node.datefield('created').strftime("%b %d, %Y")}</p>
            <p>${node.content}</p>
        </div>
    % endfor
    </div>
% endif









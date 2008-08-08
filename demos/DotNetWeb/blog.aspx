<%@ Page MasterPageFile="peace.master" Language="C#" AutoEventWireup="true" %>


<asp:content id="Content1" contentplaceholderid="TopContent" runat="server">
    <div id="callout">
	    <div id="calloutblock">
	        <h2>What's New?</h2>
	        <p>Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Nam iaculis adipiscing mi. Nulla vulputate mi at lorem. Fusce tincidunt dui non lectus euismod faucibus.</p>
	        <p><a href="#" title="link">Learn more&#8230;</a></p>
	    </div>
    </div>
</asp:content>




<asp:content id="Content2" contentplaceholderid="MainContent" runat="server">

      <DS:CmsitemControl ID="Cmsitem1" resource="blog" cachetime="1" random="false" runat="server">

          <ContentTemplate>
            <div>
                <h2><%# Container.Title %></h2>
            	<p class="date"><%# Container.Created.ToString("MMM dd, yyyy")%></p>
                <p><%# Container.Content %></p>
            </div>
          </ContentTemplate>

      </DS:CmsitemControl>

</asp:content>



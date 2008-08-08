<%@ Page MasterPageFile="peace.master" Language="C#" AutoEventWireup="true" %>

<asp:content id="Content2" contentplaceholderid="MainContent" runat="server">

    <div id="sidebar">
        <h3>Subject Title</h3>
        <p>Duis tincidunt leo eu urna. Proin auctor malesuada tellus. Praesent sit amet leo.</p>

        <p>Aenean vel augue. In hac habitasse platea dictumst. Sed pulvinar malesuada lectus. 
            Fusce sit amet erat vitae nulla varius tempus. Praesent sed elit sed turpis dignissim malesuada. 
            Sed a lectus. Sed ornare volutpat massa.
        </p>

        <p>Quisque nec neque vitae lacus ullamcorper dapibus. Phasellus et libero eget 
            felis viverra viverra. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. 
            Maecenas vitae quam commodo dui vestibulum lobortis. Mauris luctus erat a risus.</p>

        <h3>Subject Title</h3>
        <p>Duis tincidunt leo eu urna. Proin auctor malesuada tellus. Praesent sit amet leo.</p> 
    </div>

      <DS:CmsitemControl ID="featurescms" resource="features" runat="server">

          <ContentTemplate>
            <div>
                <h2><%# Container.Title %></h2>
            	<p class="date"><%# Container.Created.ToString("MMM dd, yyyy")%></p>
                <p><%# Container.Content %></p>
            </div>
          </ContentTemplate>

      </DS:CmsitemControl>
</asp:content>




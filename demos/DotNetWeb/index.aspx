<%@ Page MasterPageFile="peace.master" Language="C#" AutoEventWireup="true" %>

<asp:content id="Title1" contentplaceholderid="Title" runat="server">Demisauce Dot Net Web Demo:  Home</asp:content>

<asp:content id="Content1" contentplaceholderid="TopContent" runat="server">
    <div id="slogan">
        <img src="public/slogan-bamboo.jpg" height="310" width="303" alt="Bamboo" class="sloganfloat" />
        <h1>Demisauce</h1>
        <p>Demonstration for DotNet usage of the Demisauce server</p>
    </div>
</asp:content>




<asp:content id="Content2" contentplaceholderid="MainContent" runat="server">

      <DS:CmsitemControl resource="blog" max="1" random="true" runat="server">

          <ContentTemplate>
            <div>
                <h2><%# Container.Title %></h2>
                <!--Note, this works as well:
                    <h2><%# Container["Title"] %></h2> -->
            	<p class="date"><%# Container.Created.ToString("MMM dd, yyyy")%></p>
                <p><%# Container.Content %></p>
            </div>
          </ContentTemplate>

      </DS:CmsitemControl>


</asp:content>




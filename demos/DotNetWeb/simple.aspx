<%@ Page Language="C#" AutoEventWireup="true"  %>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml" >
<head runat="server">
    <title>Demisauce CMS API Demonstration</title>
</head>
<body>
    <div>

      <DS:CmsitemControl resource="root" runat="server">

          <ContentTemplate>

            <div style="border: 1px solid #000; padding:8px; margin:8px;">
                <b><i><u><%# Container.Title %></u></i></b> <br />
            
                <%# Container.Content %>
                <br />
                <small><%# Container.Created.ToString("MMM dd, yyyy")%></small>

            </div>
          </ContentTemplate>

      </DS:CmsitemControl>
    </div>
</body>
</html>

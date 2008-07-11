//http://weblogs.asp.net/fmarguerie/archive/2004/11/18/265719.aspx
//http://www.aspnetworld.com/articles/2004011901.aspx
using System;
using System.Web;
using System.Collections.Specialized;

namespace Demisauce
{
	/// <summary>
	/// Description of UrlRewrite.
	/// </summary>
	public class UrlRewrite : IHttpModule 
	{
		public void Init(HttpApplication Appl) {
			Appl.BeginRequest+=new System.EventHandler(Rewrite_BeginRequest);
		}

		public void Dispose() {
			//clean up
		}
		
		/// <summary>
		/// handles rewriting the http module
		/// </summary>
		public void Rewrite_BeginRequest(object sender, System.EventArgs args) {
			//process rules here
			//cast the sender to an HttpApplication object
			System.Web.HttpApplication App = (System.Web.HttpApplication)sender;
			DemisauceSettings settings = DemisauceConfiguration.Settings;

			//see if we have a match
			if(App.Request.Path.ToLower().IndexOf(settings.RewritePath.ToLower()) >= 0) 
			{
				String u = App.Request.RawUrl.ToString();
				String rid = App.Request.RawUrl.ToString();
				
				if (u.IndexOf("?") >= 0)
					u = u.Substring(u.IndexOf("?")+1);
				App.Context.RewritePath(settings.RewriteTo + "?rid=" + u ); 
			}
		}
	}
}

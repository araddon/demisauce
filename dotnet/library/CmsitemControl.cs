using System;
using System.Collections.Generic;
using System.Collections;
using System.Text;
using System.Web.UI;
using System.Web;
using System.Web.UI.HtmlControls;

namespace Demisauce
{
    public class TemplateItem : Control, INamingContainer
    {
        Cmsitem _cmsitem = null;
        Hashtable _data = new Hashtable();
        public TemplateItem(Cmsitem cmsitem)
        {
            _cmsitem = cmsitem;
        }
        public string Title
        {
            get { return this._cmsitem.Title; }
        }
        public String Content
        {
            get { return this._cmsitem.Content; }
        }
        public DateTime Created
        {
            get { return this._cmsitem.Created; }
        }
        public String Url
        {
            get { return this._cmsitem.Url; }
        }
        /// <summary>
        /// Hashtable like item that gets data from the CMSitem hashtable
        /// </summary>
        public String this[string key]
        {
            get
            {
                key = key.ToLower();
                //if (_data.Contains(key)) return _data[key].ToString();
                if (_cmsitem.Contains(key)) return _cmsitem[key].ToString();
                return "";
            }
            set
            {
                _data[key.ToLower()] = value;
            }
        }

    }

    /// <summary>
    /// Main Control for display of Demisauce Content items
    /// </summary>
    /// <example> The Tag in ASP.NET would look like this
    /// <code escaped="true">
    ///     <DS:CmsitemControl ID="Cmsitem1" resource="blog" cachetime="1" random="false" runat="server">
    ///         <ContentTemplate>
    ///             <div>
    ///                 <h2><%# Container.Title %></h2>
    ///                 <p class="date"><%# Container.Created.ToString("MMM dd, yyyy")%></p>
    ///                 <p><%# Container.Content %></p>
    ///             </div>
    ///         </ContentTemplate>
    ///     </DS:CmsitemControl>
    /// </code>
    /// </example>
    [ParseChildren(true)]
    public class CmsitemControl : DSWebControl, INamingContainer
    {
        public CmsitemControl()
        {
       
        }
        protected override void OnPreRender(EventArgs e)
        {
            EnsureChildControls();
            base.DataBind();
            base.OnPreRender(e);
        }

        [PersistenceMode(PersistenceMode.InnerProperty),
           TemplateContainer(typeof(TemplateItem))]
        public ITemplate ContentTemplate
        {
            get { return _contentTemplate; }
            set { _contentTemplate = value; }
        }private ITemplate _contentTemplate = null;

        private String Cachekey()
        {
            return String.Format("DEMISAUCE-CMS/{0}",this.Resource);
        }
        private Cmsitem[] RandomizeIfNeeded(List<Cmsitem> cmsItems)
        {
            // list is an ArrayList or Array in class.
            Random rand = new Random();
            Cmsitem[] array = new Cmsitem[cmsItems.Count];
            cmsItems.CopyTo(array);
            if (!this.Random)
                return array;

            int randIndex;
            Cmsitem tmpObj;
            for (int i = cmsItems.Count - 1; i >= 0; i--)
            {
                randIndex = rand.Next(i + 1);
                if (randIndex != i)
                {
                    tmpObj = array[i];
                    array[i] = array[randIndex];
                    array[randIndex] = tmpObj;
                }
            }
            return array;
        }
        private List<Cmsitem> GetDemisauce()
        {

            List<Cmsitem> cmsItems = (List<Cmsitem>)HttpContext.Current.Cache[this.Cachekey()];
            if (cmsItems == null)
            {
                cmsItems = Demisauce.Api.GetCmsItems(this.Resource);
                DemisauceSettings settings = DemisauceConfiguration.Settings;
                if (settings.UseCache && this.Cachetime > 0)
                {
                    HttpContext.Current.Cache.Insert(this.Cachekey(), cmsItems, null,
                        DateTime.Now.AddSeconds(this.Cachetime), TimeSpan.Zero);
                }
            }
            return cmsItems;
        }

        protected override void CreateChildControls()
        {
            // If a template has been specified, use it to create children.
            // Otherwise, create a single literalcontrol with message value
			List<Cmsitem> cmsItems = this.GetDemisauce();
            if (ContentTemplate != null)
            {
                Controls.Clear();
                
                Cmsitem[] cmsArray = this.RandomizeIfNeeded(cmsItems);
                int ct = 0;
                foreach (Cmsitem c in cmsArray)
                {
                    TemplateItem i = new TemplateItem(c);
                    ContentTemplate.InstantiateIn(i);
                    Controls.Add(i);
                    ct ++;
                    if (ct >= this.Max && this.Max > 0)
                        break;
                }
				
            }
            else if (cmsItems == null)
            {
                // build a default set of div output, user could style with CSS using cascading
                Controls.Clear();
                HtmlControl baseItem = new HtmlGenericControl("div");
                this.Controls.Add(baseItem);
                baseItem.Controls.Add(new LiteralControl("<!-- No Demisauce Connection -->"));
            }
            else
            {
                // build a default set of div output, user could style with CSS using cascading
                Controls.Clear();
                HtmlControl baseItem = new HtmlGenericControl("div");
                this.Controls.Add(baseItem);
                foreach (Cmsitem c in cmsItems)
                {
                    HtmlControl cmsdiv = new HtmlGenericControl("div");
                    baseItem.Controls.Add(cmsdiv);
                    HtmlControl titleDiv = new HtmlGenericControl("div");
                    cmsdiv.Controls.Add(titleDiv);
                    titleDiv.Controls.Add(new LiteralControl(c.Title));
                    HtmlControl contentDiv = new HtmlGenericControl("div");
                    cmsdiv.Controls.Add(contentDiv);
                    contentDiv.Controls.Add(new LiteralControl(c.Content));
                }
            }
        }
        /// <summary>
        /// Resource ID
        /// </summary>
        public String Resource
        {
            set { this._resource = value; }
            get { return this._resource; }
        }private string _resource = String.Empty;

        /// <summary>
        /// Maximum # of items to show
        /// </summary>
        public int Max
        {
            set { this._maxCount = value; }
            get { return this._maxCount; }
        }private int _maxCount = -1;

        /// <summary>
        /// Randomize from list, used by itself it randomizes the order of items.
        /// Used in conjunction with Max, can select just a limited number of items to show randomly.
        /// </summary>
        public bool Random
        {
            set { this._random = value; }
            get { return this._random; }
        }private bool _random = false;
    }   
}

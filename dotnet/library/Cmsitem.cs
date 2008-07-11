using System;
using System.Collections.Generic;
using System.Collections;
using System.Text;
using System.Xml;

namespace Demisauce
{
    /// <summary>
    /// CmsItem:   wraps a content item
    /// </summary>
    public class Cmsitem : System.Collections.Hashtable
    {   
        public Cmsitem(XmlNode cmsNode)
        {
            this.Init(cmsNode);
        }
        /// <summary>
        /// Initilization, load properties from xml node
        /// </summary>
        /// <param name="cmsNode"></param>
        private void Init(XmlNode cmsNode)
        {
            if (cmsNode.Attributes["id"] != null) _id = Convert.ToInt32(cmsNode.Attributes["id"].Value);
            if (cmsNode.Attributes["key"] != null) _key = Convert.ToString(cmsNode.Attributes["key"].Value);
            foreach (XmlNode fieldNode in cmsNode.ChildNodes)
            {
                if (fieldNode.NodeType == XmlNodeType.CDATA)
                {
                    this.Add(fieldNode.Name, fieldNode.FirstChild.Value.Trim());
                }
                else
                {
                    this.Add(fieldNode.Name, fieldNode.InnerText.Trim());
                }
            }
            if (this.Contains("content")) _content = this["content"].ToString();
            if (this.Contains("title")) _title = this["title"].ToString();
            if (this.Contains("created")) _createDate = Convert.ToDateTime(this["created"]);
            if (this.Contains("url")) _url = this["url"].ToString();
        }
        public int ID
        {
            set { this._id = value; }
            get { return this._id; }
        }private Int32 _id = 0;
        public string Key
        {
            set { this._key = value; }
            get { return this._key; }
        }private string _key = String.Empty;
        public string Url
        {
            set { this._url = value; }
            get { return this._url; }
        }private string _url = String.Empty;
        public DateTime Created
        {
            set { this._createDate = value; }
            get { return this._createDate; }
        }private DateTime _createDate = DateTime.Now;
        public string Content
        {
            set { this._content = value; }
            get { return this._content; }
        }private string _content = String.Empty;
        public string Title
        {
            set { this._title = value; }
            get { return this._title; }
        }private string _title = String.Empty;
    }
}

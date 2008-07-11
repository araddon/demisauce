using System;
using System.Collections.Generic;
using System.Collections;
using System.Text;
using System.Xml;

namespace Demisauce
{
    /// <summary>
    /// Email template:   gets xml node into .net object
    /// </summary>
    public class EmailTemplate : System.Collections.Hashtable
    {
        // fields
        private Int32 _id = 0;
        private string _key = String.Empty;
        //private Hashtable _data = new Hashtable();
        private string _template = String.Empty;
        private string _subject = String.Empty;
        public EmailTemplate(XmlNode emailNode)
        {
            this.Init(emailNode);
        }
        /// <summary>
        /// Initilization, load properties from xml node
        /// </summary>
        /// <param name="cmsNode"></param>
        private void Init(XmlNode xmlNode)
        {
            if (xmlNode.Attributes["id"] != null) _id = Convert.ToInt32(xmlNode.Attributes["id"].Value);
            if (xmlNode.Attributes["key"] != null) _key = Convert.ToString(xmlNode.Attributes["key"].Value);
            foreach (XmlNode fieldNode in xmlNode.ChildNodes)
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
            if (this.Contains("template")) _template = this["template"].ToString();
            if (this.Contains("subject")) _subject = this["subject"].ToString();
        }
        public int ID
        {
            set { this._id = value; }
            get { return this._id; }
        }
        public string Key
        {
            set { this._key = value; }
            get { return this._key; }
        }
        public string Template
        {
            set { this._template = value; }
            get { return this._template; }
        }
        public string Subject
        {
            set { this._subject = value; }
            get { return this._subject; }
        }
    }
}
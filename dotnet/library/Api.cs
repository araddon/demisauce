using System;
using System.Collections.Generic;
using System.Text;
using System.Xml;

namespace Demisauce
{
	public class DemisauceConnectionException : Exception
	{
		
	}
    public class Api
    {
        /// <summary>
        /// Get and return a list of CmsItems
        /// </summary>
        /// <returns>List of cmsitems, or null if none</returns>
        public static List<Cmsitem> GetCmsItems(string resource)
        {
            List < Cmsitem > cmsItems = new List<Cmsitem>();
            XmlNode itemsNode = GetRootNode("cms",resource);
            if (itemsNode is XmlNode)
            {
                foreach (XmlNode cmsNode in itemsNode.ChildNodes)
                {
                    cmsItems.Add(new Cmsitem(cmsNode));
                }
            }
            else
            {
                //TODO:  handle error
            }
            return cmsItems;
        }
        /// <summary>
        /// Gets the root XmlNode of a demisauce response
        /// </summary>
        /// <param name="method">Method name (email, cms, etc) See Demisauce.org for list</param>
        /// <returns></returns>
        private static XmlNode GetRootNode(string method,string resource)
        {
            XmlTextReader reader = null;

            try
            {
                DemisauceSettings settings = DemisauceConfiguration.Settings;
                // Load the reader with the data file and ignore all white space nodes.         
                reader = new XmlTextReader(String.Format("{0}/api/xml/{1}/{2}?apikey={3}",
                        settings.Location,
                        method,
                        resource,
                        settings.ApiKey));
                reader.WhitespaceHandling = WhitespaceHandling.None;
                XmlDocument xmldoc = new XmlDocument();
                xmldoc.Load(reader);
                if (xmldoc.HasChildNodes && xmldoc.FirstChild.NextSibling != null)
                {
                    if (xmldoc.FirstChild.NextSibling.Name == "demisauce")
                    {
                        return xmldoc.FirstChild.NextSibling;
                    }
                    else
                    {   
                        // an exception
                        Console.WriteLine(xmldoc.FirstChild.NextSibling.OuterXml);
                    }
                }
            }
            catch (Exception ex)
            {
            	// what to do?
            	throw new Exception("No connection can be established to Demisauce Server",ex);
            }
            finally
            {
                if (reader != null)
                    reader.Close();
            }
            return null;
        }
    }
}

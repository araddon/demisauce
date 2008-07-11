using System;
using System.Configuration;
using System.Xml;


namespace Demisauce
{
    /// <summary>
    /// The configuration handler to allow normal app.config, or web.config sections
    /// for Demisauce.  See  "example_app.config" file.
    /// </summary>
    class DemisauceConfiguration : IConfigurationSectionHandler
    {
        private static string ConfigSection = "Demisauce";
        private static DemisauceSettings settings;

        public DemisauceConfiguration()
        {
        }

        public static DemisauceSettings Settings
        {
            get
            {
                if (settings == null)
                {
                    settings = (DemisauceSettings)ConfigurationSettings.GetConfig(ConfigSection);
                }

                return settings;
            }
        }

        public object Create(object parent, object configContext, XmlNode section)
        {
            ConfigSection = section.Name;
            return new DemisauceSettings(section);
        }
    }
    /// <summary>
    /// Configuration settings for Demisauce API Library.
    /// </summary>
    /// <remarks>
    /// <p>First, register the configuration section in the configSections section:</p>
    /// <p><code>&lt;configSections&gt;
    /// &lt;section name="Demisauce" type="Demisauce.DemisauceConfiguration,Demisauce"/&gt;
    /// &lt;/configSections&gt;</code>
    /// </p>
    /// <p>
    /// Next, include the following config section:
    /// </p>
    /// <p><code>
    /// 	&lt;Demisauce 
    /// location="http://yourserver.com:4950/"	// optional
    /// apiKey="1234567890abc"	// required
    /// cacheDuration="ssss"	// optional, defaults to 3600 seconds (1 hour)
    /// rewritepath="/c/"       // path in uri to look for, if it exists will rewrite urls
    /// rewriteto="cmsitem.aspx"  // aspx page to rewrite to
    /// &gt;
    /// &lt;/Demisauce&gt;
    /// </code></p>
    /// </remarks>
    internal class DemisauceSettings
    {
        private string _apiKey;
        private string _location = "http://localhost:4950/";
        private int _cacheDuration = 3600;
        private string _rewritePath = String.Empty;
        private string _rewriteTo = "cmsitem.aspx";
        private string _cacheLocation;
        private bool _useCache = true;
        /// <summary>
        /// Loads configuration settings in the config file.
        /// </summary>
        /// <param name="configNode">XmlNode containing the configuration settings.</param>
        public DemisauceSettings(XmlNode configNode)
        {
            if (configNode == null) throw new ArgumentNullException("configNode");

            foreach (XmlAttribute attribute in configNode.Attributes)
            {
                switch (attribute.Name.ToLower())
                {
                    case "apikey":
                        _apiKey = attribute.Value;
                        break;
                    case "location":
                        _location = attribute.Value;
                        break;
                    case "rewritepath":
                        _rewritePath = attribute.Value;
                        break;
                    case "rewriteto":
                        _rewriteTo = attribute.Value;
                        break;
                    case "usecache":
                        try
                        {
                            _useCache = bool.Parse(attribute.Value);
                            break;
                        }
                        catch (FormatException ex)
                        {
                            throw new System.Configuration.ConfigurationException("usecache should be \"true\" or \"false\"", ex, configNode);
                        }
                    case "cacheduration":
                        try
                        {
                            _cacheDuration = Convert.ToInt32(attribute.Value);
                            break;
                        }
                        catch (FormatException ex)
                        {
                            throw new System.Configuration.ConfigurationException("cache Duration should be seconds value (1234)", ex, configNode);
                        }
                    case "cachelocation":
                        _cacheLocation = attribute.Value;
                        break;

                    default:
                        throw new System.Configuration.ConfigurationException(String.Format("Unknown attribute '{0}' in Demisauce configuration", attribute.Name), configNode);
                }
            }
        }

        /// <summary>
        /// API key, required
        /// </summary>
        public string ApiKey
        {
            get { return _apiKey; }
        }
        /// <summary>
        /// location key, optional (default = http://localhost:4950  )
        /// </summary>
        public string Location
        {
            get { return _location; }
        }
        /// <summary>
        /// which uri path to look for and then rewrite
        /// so:
        /// /c/my_about_page.aspx  
        /// 
        /// gets rewritten to
        /// 
        /// cmsitem.aspx?rid=my_about_page
        /// </summary>
        public string RewritePath
        {
            get { return _rewritePath; }
        }
        /// <summary>
        /// File (ASPX) to rewrite urls to that are found in url path 
        /// of "RewritePath"
        /// </summary>
        public string RewriteTo
        {
            get { return _rewriteTo; }
        }
        /// <summary>
        /// Cache usage
        /// </summary>
        public bool UseCache
        {
            get { return _useCache; }
        }

        /// <summary>
        /// Cache duration in seconds
        /// </summary>
        public int CacheDuration
        {
            get { return _cacheDuration; }
        }

        public string CacheLocation
        {
            get { return _cacheLocation; }
        }
    }
}

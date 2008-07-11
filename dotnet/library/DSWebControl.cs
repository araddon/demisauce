using System;
using System.Collections.Generic;
using System.Text;
using System.Web.UI;

namespace Demisauce
{
    public class DSWebControl : Control
    {
        /// <summary>
        /// Cachetime (In seconds) to cache this item/list
        /// </summary>
        public int Cachetime
        {
            set { this._cachetime = value; }
            get 
            {
                if (this._cachetime == -10)
                {
                    this._cachetime = DemisauceConfiguration.Settings.CacheDuration;
                }
                return this._cachetime; 
            }
        }private int _cachetime = -10;

        /// <summary>
        /// ResourceID(Key) of the item/items to get
        /// </summary>
        public String ResourceID
        {
            set { this._resourceid = value; }
            get { return this._resourceid; }
        }private string _resourceid = String.Empty;
    }   
}

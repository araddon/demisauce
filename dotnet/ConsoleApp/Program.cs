using System;
using System.Collections.Generic;
using System.Text;
using System.Web;
using System.Net;
using System.IO;
using System.Xml;
using Demisauce;

namespace ConsoleApplication1
{
    class Program
    {
        static void Main(string[] args)
        {
            List<Cmsitem> cmsItems = Demisauce.Api.GetCmsItems("root");
            foreach (Cmsitem c in cmsItems)
            {
                Console.WriteLine("<item id=\"" + c.ID.ToString() + "\" key=\"" + c.Key + "\" >");

                foreach (string key in c.Keys)
                {
                    Console.WriteLine("\t<" + key + ">" + c[key] + "<" + key + ">");
                }
                Console.WriteLine("</item>");
            }
        }
    }
}

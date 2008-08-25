<?php  
/**
 * demisauce PHP Library
 *
 * A php library to the demisauce server Services
 *
 * @package     demisauce
 * @author      Aaron Raddon
 * @copyright   Copyright (c) 2008, Aaron Raddon
 * @license     http://code.google.com/p/demisauce/source/browse
 * @link        http://demisauce.org
 * @filesource
 */

class CmsItem {
    
}
class Demisauce {

    var $cache      = 0;
    var $apiver     = "/api/";
    var $demisauce_key  = "";
    var $getitems           = array();
    var $demisauce_base_url   = "http://www.demisauce.com";
    /**
     * Constructor
     *
     * @access  public
     */
    function Demisauce($props = array())
    {
        if (count($props) > 0)
        {
            $this->initialize($props);
        }
        
        log_message('debug', "Demisauce Library Class Initialized");
    }
    
    // --------------------------------------------------------------------
    /**
     * Initialize preferences
     *
     * @access  public
     * @param   array
     * @return  void
     */ 
    function initialize($config = array())
    {
        $defaults = array(
                            'cache'         => 0,
                            'demisauce_key'     => "",
                            'getitems'          => array(),
                            'demisauce_base_url'        => "http://www.demisauce.com"
                        );  
        
        foreach ($defaults as $key => $val)
        {
            if (isset($config[$key]))
            {
                $method = 'set_'.$key;
                if (method_exists($this, $method))
                {
                    $this->$method($config[$key]);
                }
                else
                {
                    $this->$key = $config[$key];
                }           
            }
            else
            {
                $this->$key = $val;
            }
        }
    }
    
    public function get_ds_ws($resource_id,$dstype,$format='xml')
    {
        $ds_url =  $this->demisauce_base_url.$this->apiver.$format.'/'.$dstype.'/';
        $ds_url =  $ds_url.$resource_id.'?apikey='.$this->demisauce_key;
        try {
            $response = file_get_contents($ds_url);
            //echo $ds_url;
            if ($response === FALSE) {
                return FALSE;
            }
            $xml = simplexml_load_string($response);
            return $xml;
        } catch (Exception $e) {
            #echo 'Caught exception: ',  $e->getMessage(), "\n";
            return FALSE;
        }
    }
    /**
     * Get a CMS Xml item
     *
     * @access  public
     * @param   string resource id for cms item
     * @param   string format  ('xml' or 'html' )
     * @return  xml node
     */
    public function get_cms($resource,$format='xml')
    {
        return $this->get_ds_ws($resource,'cms',$format);
    }
    /**
     * Get Poll Html
     *
     * @access  public
     * @param   string resource id for poll
     * @return  html 
     */
    public function get_poll_xml($poll)
    {  
        $ds_poll_xml = $this->get_ds_ws($poll,'poll','xml');
        $html = '';
        foreach ($ds_poll_xml as $poll) {
             $html = $html.$poll->html;
        }
        # only returning the first
        return $ds_poll_xml[0]->poll;
    }
    // --------------------------------------------------------------------
    
    /**
     * Set Demisauce Key
     *
     * @access  public
     * @param   string
     * @return  void
     */ 
    function set_demisauce_key($key)
    {
        $this->demisauce_key = $key;
    }
    // --------------------------------------------------------------------
    
    /**
     * Set Demisauce base url
     *
     * @access  public
     * @param   string
     * @return  void
     */ 
    function set_demisauce_base_url($url)
    {
        $this->demisauce_base_url = $url;
    }
}

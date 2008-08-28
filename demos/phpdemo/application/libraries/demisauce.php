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
 */
 

function demisauce_html($service, $resource_id){
    //return 'here it is';
}
class DemisauceServiceBase {
    function __construct($props = array()){
        $this->initialize($props);
    }
    function initialize($setas = array()) {
        foreach ($setas as $key => $val) {
            $method = 'set_'.$key;
            if (method_exists($this, $method)) {
                $this->$method($val);
            } else {
                $this->$key = $val;
            }           
        }
    }
    public function debug_info(){
        $html = "";
        $class_vars = get_class_vars(get_class($this));
        foreach ($class_vars as $name => $value) {
            $html = $html."$name : ".$this->$name."<br />";
        }
        return $html;
    }
}

class DemisauceServiceResponse extends DemisauceServiceBase
{
    var $success = False;
    var $data;
    var $service = 'servicename';
    var $message = 'new response, no message yet';
    var $format = 'xml';
    var $xml;
    var $url = '';
    function __construct($props){
        parent::__construct($props);
    }
}

class DemisauceService extends DemisauceServiceBase {
    var $key_format = '{app_slug}/{class_name}/{local_key}';
    var $url_format = "{base_url}/api/{format}/{service}/{key}?apikey={api_key}";
    var $service = 'service';
    var $method_url; // if not same as service
    var $format = 'xml';
    var $app_slug = 'demisauce';
    var $cache = True;
    var $data = array();
    var $isdefined = False;
    //var $method_url = None
    //var $service_registry = None
    var $api_key = '';
    var $base_url = 'http://www.demisauce.com';
    
    function __construct($props){
        parent::__construct($props);
    }
    public function fetch($resource_id,$format='xml') {
        //echo "ARGS2:  $resource_id , $format , <br/>";
        $ds_url =  $this->url_formatter(array(
            'key' => $resource_id,
            'format' => $format
        ));
        //echo "ds_url. = $ds_url<br />";
        $response = new DemisauceServiceResponse(array(
            'service' => $this->service,
            'format' => $format,
            'url' => $ds_url
        ));
        try {
            
            $response->data = file_get_contents((string)$ds_url);
            
            if ($response->data === FALSE) {
                //TODO:  get http response code
                $response->message = 'failure, no response';
                return $response;
            }
            if ($format == 'xml') {
                $response->xml = simplexml_load_string($response->data);
                $response->success = true;
                //echo $response->data;
                return $response;
            } else {
                $response->success = true;
                return $response;
            }

        } catch (Exception $e) {
            // TODO:  add error message from exception
            //echo 'CRAPOLO, bad response';
            $response->message = 'failure, error on response';
            return $response;
        }
    }
    public function url_formatter($suba = array()){
        if (is_null($this->url_format)){
            
            return $this->base_url."/".$this->method_url;
            
        } else {
            
            $url_format = $this->url_format;
            $sub_dict = get_class_vars(get_class($this));
            
            foreach ($sub_dict as $key => $value) {
                if (is_string($value)){
                    $url_format = str_replace("{".$key."}",$this->$key,$url_format);
                }
            }
            foreach ($suba as $key => $value) {
                $url_format = str_replace("{".$key."}",$value,$url_format);
            }
            return $url_format;
        }
    }
}
class Demisauce extends DemisauceServiceBase{

    var $cache                = 0;
    var $memcached;
    var $apiver               = "/api/";
    static $api_key              = "";
    //var $getitems             = array();
    public static $service_app_slug     = 'demisauce';
    public static $base_url             = "http://www.demisauce.com";
    public static $this_app_slug        = 'yourphpapp';
    public static $demisauce_base_url = 'http://www.demisauce.com';
    private $service_reg      = array();
    public static $service_app_slug2    = 'demisauce';

    function __construct($props = array()) {
        parent::__construct();
        if (count($props) > 0) {
            $this->initialize($props);
        }
    }
    static private $m_demisauce_app = NULL; 
    public static function get_app() {
        if (self::$m_demisauce_app == NULL) {
            self::$m_demisauce_app = new Demisauce();
        }
        return self::$m_demisauce_app;
    }
    private function check_cache() {
        
    }
    public function get_service($resource,$service='',$format='xml',$app='demisauce'){
        //echo "ARGS1:  $resource , $service , $format , $app <br/>";
        if ($app == '') {
            $app = $this->service_app_slug;
        }
        $serviceapp = $service."/".$app;
        $dss;
        if (!in_array($serviceapp,$this->service_reg)){
            // TODO:  check cache 
            $service_def = new  DemisauceService(array(
                'service'    => 'service',
                'api_key'    => Demisauce::$api_key,
                'base_url'   => Demisauce::$demisauce_base_url,
                
            ));
            $response = $service_def->fetch($app."/".$service);
            //echo $response->xml;
            if ($response->success){
                // prep the intended service
                $dss = new DemisauceService(array(
                    'service'    => $service,
                    'api_key'    => Demisauce::$api_key,
                    'base_url'   => Demisauce::$base_url,
                    'app_slug'   => $app,
                    'format'     => $format
                ));
                // should be one service
                $response->success = false;
                foreach ($response->xml as $svc_xml) {
                    $response->success = true;
                    if (property_exists($svc_xml, 'base_url')) {
                        $dss->base_url = $svc_xml->base_url;
                    }
                    if (property_exists($svc_xml, 'method_url') && $svc_xml->method_url != 'None') {
                        $dss->method_url = $svc_xml->method_url;
                    }
                    if (property_exists($svc_xml, 'url_format') && $svc_xml->url_format != 'None') {
                        $dss->url_format = $svc_xml->url_format;
                    } else {
                        $dss->url_format = null;
                    }
                }
                // add service base to registry
                if ($response->success){
                    $this->service_reg[$serviceapp] = $dss;
                }
            } else {
                return false;
            }
        } else {
            $dss = $this->service_reg[$serviceapp];
        }
        
        $response = $dss->fetch($resource,$format);
        return $this->get_response($response);
    }
    private function get_response($response){
        if (!is_null($response) && ($response->success == true)){
            if ($response->format == 'xml'){
                return $response->xml;
            } else if ($response->format == 'view'){
                return $response->data;
            } else {
                return $response->data;
            }
        } else {
            return $response->message;
        }
    }
    public function get_cms($resource,$format='xml') {
        $content = $this->get_service($resource,$service='cms',$format='xml',$app='demisauce');
        return $content;
    }
    public function get_poll($resource) {
        $content = $this->get_service($resource,$service='poll',$format='xml',$app='demisauce');
        return $content[0]->poll->html;
    }
}

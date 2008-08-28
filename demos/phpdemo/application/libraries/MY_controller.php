<?php
require_once APPPATH.'libraries/demisauce.php';

Demisauce::$api_key = "a95c21ee8e64cb5ff585b5f9b761b39d7cb9a202";
Demisauce::$demisauce_base_url   = "http://localhost:4951";
Demisauce::$base_url   = "http://localhost:4951";
Demisauce::$this_app_slug = "phpdemo";


class MY_Controller extends Controller {

    public $path = '/content/';
    public $data = array("title" => "Demisauce.org information web site");
    public $dsService;
    
    function MY_Controller()
    {
        parent::Controller();   
        //$config['demisauce_base_url'] = $this->config->item('demisauce_base');
        //$config['demisauce_key'] = $this->config->item('demisauce_key');
        //$this->load->library('demisauce', $config);
        $this->data = $this->_prep_page();
        $this->dsService = Demisauce::get_app();
    }
    function _prep_page()
    {
        $data['title'] = 'Demisauce.org information web site';
        $data['demisauce_base_url'] = $this->config->item('demisauce_base');
        $data['path'] = $this->path;
        return $data;
    }
    function _header()
    {
        $xml = $this->dsService->get_cms('root');
        $this->data['nav_array'] = $xml[0]->cmsitem;
        $this->data['body_content'] = '';
        $this->load->view('_header.html',$this->data);
    }
    function _footer()
    {
        $this->load->view('_footer.html',$this->data);
    }
    function _render($data)
    {
        $this->load->view('_header.html',$data);
        $this->load->view('content.php',$data);
        $this->load->view('_footer.html',$data);
    }
    function getcontent()
    {
        $arr = $this->uri->segment_array();
        unset($arr[1]);
        $ds_url = implode('/', $arr);
        
        $ds_cmsxml = $this->dsService->get_cms($ds_url);
        
        
        $this->output->cache(0);
        if ($ds_cmsxml !== FALSE) {
            if ($ds_cmsxml->attributes()->len == '1') {
                $data['title'] = $ds_cmsxml[0]->cmsitem->title;
            }
        }
        $this->data['body_xml'] = $ds_cmsxml;
        //$this->_render($data);
        return $this->data;
    }
}

?>
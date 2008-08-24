<?php

class MY_Controller extends Controller {

    public $path = '/content/';
    public $data = array("title" => "Demisauce.org information web site");
    function MY_Controller()
    {
        parent::Controller();   
        $config['demisauce_base_url'] = $this->config->item('demisauce_base');
        $config['demisauce_key'] = $this->config->item('demisauce_key');
        $this->load->library('demisauce', $config);
        $this->data = $this->_prep_demisauce($this->data);
    }
    function _prep_demisauce()
    {
        $data['title'] = 'Demisauce.org information web site';
        $data['demisauce_base_url'] = $this->config->item('demisauce_base');
        $data['path'] = $this->path;
        return $data;
    }
    function _header()
    {
        $xml = $this->demisauce->get_cms('root');
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
        
        $ds_cmsxml = $this->demisauce->get_cms($ds_url);
        $this->data['ds_poll_html'] = $this->demisauce->get_poll_html('what-should-the-new-features-be');
        
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
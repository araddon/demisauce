<?php
class Content extends Controller {
    
    private $path = '/content/';
    function Content()
    {
         parent::Controller();
         $config['base_url'] = $this->config->item('demisauce_base');
         $config['demisauce_key'] = $this->config->item('demisauce_key');
         $this->load->library('demisauce', $config);
    }
    function _prep_demisauce($data)
    {
        $data['title'] = 'Demisauce.org information web site';
        $data['base_url'] = $this->config->item('demisauce_base');
        $data['path'] = $this->path;
        return $data;
    }
    function _ds_nav_array($ds_resource_id = '')
    {
        $xml = $this->demisauce->get_cms($ds_resource_id);
        
        $nav_array = $xml[0]->cmsitem;
        return $nav_array;
    }
    function _render($data)
    {
        $this->load->view('_header.html',$data);
        $this->load->view('content.php',$data);
        $this->load->view('_footer.html',$data);
    }
    function index()
    {
        $this->getcontent('root');
    }
    function getcontent()
    {
        
        $arr = $this->uri->segment_array();
        unset($arr[1]);
        $ds_url = implode('/', $arr);
        $ds_cmsxml = $this->demisauce->get_cms($ds_url);
        $data['ds_poll_html'] = $this->demisauce->get_poll_html('what-features-do-we-want-in-demisauce');
        $data = $this->_prep_demisauce($data);
        $this->output->cache(0);
        if ($ds_cmsxml !== FALSE) {
            if ($ds_cmsxml->attributes()->len == '1') {
                $data['title'] = $ds_cmsxml[0]->cmsitem->title;
            }
        }
        $data['nav_array'] = $this->_ds_nav_array('root');
        $data['body_content'] = '';
        $data['body_xml'] = $ds_cmsxml;
        $this->_render($data);
    }
}
?>
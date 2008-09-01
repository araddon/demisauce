<?php
require_once APPPATH.'libraries/demisauce.php';

class Service extends MY_Controller {

    function __construct()
    {
        parent::MY_Controller();
    }
    function index()
    {
        $this->_header();
        $this->data['body_xml'] = null;
        $content = $this->dsService->get_service($resource='',$service='helloworld',$format='view',$app='djangodemo');
        $this->data['body_content'] = $content;
        $this->load->view('content',$this->data);
        $this->_footer();
    }
    function helloworld($name='World')
    {
        print 'This is the Hello '.$name.' From php.  It is showing in another app hopefully!';
    }
}

/* End of file test.php */
?>
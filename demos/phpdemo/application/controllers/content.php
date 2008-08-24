<?php
class Content extends MY_Controller {
    
    
    function Content()
    {
        parent::MY_Controller();
    }
    function showcontent()
    {
        $data = $this->getcontent();
        $this->_header();
        $this->load->view('content',$data);
        $this->_footer();
    }
    function index()
    {
        $data = $this->getcontent('root');
        $this->_header();
        $this->load->view('content',$data);
        $this->_footer();
    }
}
?>
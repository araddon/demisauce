<?php
class Content extends MY_Controller {
    
    
    function Content()
    {
        parent::MY_Controller();
    }
    function showcontent()
    {
        $this->data['ds_poll_xml'] = $this->dsService->get_service('what-should-the-new-features-be','poll');
        $data = $this->getcontent();
        $this->_header();
        $this->load->view('content',$data);
        $this->_footer();
    }
    function index()
    {
        $this->data['ds_poll_xml'] = $this->dsService->get_service('what-should-the-new-features-be','poll');
        $data = $this->getcontent('root');
        $this->_header();
        $this->load->view('content',$data);
        $this->_footer();
    }
}
?>
<?php



class Test extends MY_Controller {

	function Test()
	{
		parent::MY_Controller();
	}
	
	function index()
	{
        $this->_header();
        //$this->data['ds_poll_xml'] = $this->demisauce->get_poll_xml('what-should-the-new-features-be');
        //$this->data['ds_poll_html'] = $this->dsService->get_poll('what-should-the-new-features-be');
        $this->data['ds_comment'] = $this->dsService->get_service('demisauce.com','comment','view');
        $this->data['ds_django_hello'] = $this->dsService->get_service($resource='',$service='helloworld',$format='view',$app='djangodemo');
        $this->load->view('demisauce-tests',$this->data);
        $this->_footer();
	}
}

/* End of file test.php */
?>
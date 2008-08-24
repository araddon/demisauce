<?php



class Test extends MY_Controller {

	function Test()
	{
		parent::MY_Controller();
	}
	
	function index()
	{
        $this->_header();
        $this->data['ds_poll_html'] = $this->demisauce->get_poll_html('what-should-the-new-features-be');
        $this->load->view('demisauce-tests',$this->data);
        $this->_footer();
	}
}

/* End of file test.php */
?>
<?php



class Service extends MY_Controller {

	function Service()
	{
		parent::MY_Controller();
	}
	
	function index()
	{
        $this->_header();
        
        $this->_footer();
	}
	function helloworld($name='World')
	{
        print 'This is the Hello '.$name.' From php';
	}
}

/* End of file test.php */
?>
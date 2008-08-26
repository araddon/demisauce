<?php



class Test extends MY_Controller {

	function Test()
	{
		parent::MY_Controller();
	}
	
	function index()
	{
        $this->_header();
        try {
            //$memcached = new Memcache;
            //$memcached->connect('192.168.125.133', 11211);
            $this->data['ds_comment'] = $this->demisauce->get_ds_ws('person','comment','view');
            
        } catch (Exception $e) {
            echo 'no memcached for you';
        }

        
        $this->data['ds_poll_xml'] = $this->demisauce->get_poll_xml('what-should-the-new-features-be');
        $this->load->view('demisauce-tests',$this->data);
        $this->_footer();
	}
}

/* End of file test.php */
?>
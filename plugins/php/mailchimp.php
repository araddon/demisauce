<?php
/*  mailchimp integration (gearman workers)

run:   php -f mailchimp.php 
in supervisor conf:

*/
require_once 'config.php';
require_once 'lib/MCAPI.class.php';
require_once( 'lib/class-json.php' );

$worker= new GearmanWorker();
foreach ($gearman_servers as $server => $port){
  echo 'gearman servers = '.$server.':'.$port.'  ';
  $worker->addServer($server,$port);
}

$worker->addFunction("mailchimp_addtolist", "mailchimp_addtolist");

while ($worker->work());

/*
Ensure the Segments (InterestGroups) exist on Mailchimp, if not create them
*/
function ensure_segments($api, $list_id,$new_segments){
  $retval = $api->listInterestGroups($list_id);
  $segments = array();
  echo '0 group ='.$retval['name']." = ".$retval['form_field']."\n";
  foreach ($retval['groups'] as $name => $val){
    echo '1 group ='.$name." = ".$val."\n";
    array_push($segments, $val);
  }
  foreach ($new_segments as $segment){
    if (!in_array($segment, $segments)) {
      echo "does NOT have segment: creating ->".$segment."\n";
      $retval = $api->listInterestGroupAdd($list_id, $segment);
      echo "Retval = ".$retval."\n";
    }
  }
}
/*  Adds user to Email List and segments, expects json args like so:
  {
       'user':{"email":"araddon+4@gmail.com"},
       'mailchimp_listid':'12345',
       'mailchimp_api_key':'abc',
       'attributes':[{"name":"BetaUsers","category":"event"},{"name":"NewSegment3","category":"event"}]
  }
*/
function mailchimp_addtolist($job){
  $job_json;
  echo $job->workload()."\n\n";
  if (function_exists('json_encode')) {
    // Use the built-in json_encode function if it's available
    $job_json = json_decode($job->workload());
  } else {
    $json = new Services_JSON();
    $job_json = $json->decode($job->workload());
  }
  //API Key - see http://admin.mailchimp.com/account/api
  $mailchimp_apikey = $job_json->mailchimp_api_key;
  $list_id = $job_json->mailchimp_listid;
  $api = new MCAPI($mailchimp_apikey);
  echo "Getting list_id=".$list_id." with key= ".$mailchimp_apikey."\n";
  
  $merge_vars = array('FNAME'=>'aaron', 'LNAME'=>'@gmail', 'INTERESTS'=>'');
  // By default this sends a confirmation email - you will not see new members
  // until the link contained in it is clicked!
  $optin = false;
  $update_existing = true; // don't return error if allready existing
  $user_email = $job_json->user->email;
  echo 'emails ='.$job_json->user->email."\n";
  $retval = '';
  if (property_exists($job_json->user, 'attributes')) {
    $segments = array();
    foreach ($job_json->user->attributes as $segment){
      if ($segment->category == 'notification' || $segment->category == 'event'){
        array_push($segments, $segment->name);
        $merge_vars['INTERESTS'] = $merge_vars['INTERESTS'].$segment->name.',';
      }
    }
    ensure_segments($api, $list_id,$segments);
  }
  
  echo 'segments ='.$merge_vars['INTERESTS']."\n";
  echo 'calling mailchimp w email ='.$user_email."\n";
  $retval = $api->listSubscribe( $list_id, $user_email, $merge_vars ,'html'
        ,$optin,$update_existing);
  
  if ($api->errorCode){
    echo "Unable to load listSubscribe()!\n";
    echo "\tCode=".$api->errorCode."\n";
    echo "\tMsg=".$api->errorMessage."\n";
    return 0;
  } else {
    echo "Returned: ".$retval."\n";
    return 1;
  }
}
?>
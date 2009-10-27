http://dev.mysql.com/doc/refman/5.0/en/alter-table.html
ADD [COLUMN] col_name column_definition [FIRST | AFTER col_name ]
MODIFY [COLUMN] col_name column_definition [FIRST | AFTER col_name]
10/23/09:
ALTER TABLE comment ADD is_public tinyint(1) default '0' after `isuser`;


1/20/09 
#NOT YET: ALTER TABLE activity ADD ip varchar(16) NOT NULL after `ref_url`;

----- Implemented   
CREATE TABLE `poll` (
  `id` int(11) NOT NULL auto_increment,
  `site_id` int(11) default 0,
  `person_id` int(11) default NULL,
  `name` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `description` varchar(500) default NULL,
  `html` text,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`),
  CONSTRAINT `poll_site_fk` FOREIGN KEY (`site_id`) REFERENCES `site` (`id`),
  CONSTRAINT `poll_person_fk` FOREIGN KEY (`person_id`) REFERENCES `person` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*
CREATE TABLE `poll_answer` (
  `id` int(11) NOT NULL auto_increment,
  `question_id` int(11) default NULL,
  `value` varchar(1) default NULL,
  `value_long` varchar(500) default NULL,
  PRIMARY KEY  (`id`),
  KEY `question_id` (`question_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8

CREATE TABLE `poll_question` (
  `id` int(11) NOT NULL auto_increment,
  `poll_id` int(11) default NULL,
  `question` varchar(255) NOT NULL,
  `type` varchar(10) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `poll_id` (`poll_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8

# if doing InnoDB
CREATE TABLE `poll_question` (
  `poll_id` int(11) NOT NULL,
  `question_id` int(11) NOT NULL,
  KEY `poll_id` (`poll_id`),
  KEY `question_id` (`question_id`),
  CONSTRAINT `poll_question_fk_poll` FOREIGN KEY (`poll_id`) REFERENCES `poll` (`id`),
  CONSTRAINT `poll_question_fk_question` FOREIGN KEY (`question_id`) REFERENCES `question` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
*/

ALTER TABLE person ADD CONSTRAINT UniqueEmailPerSite UNIQUE (email,site_id);
ALTER TABLE site CHANGE commenturl site_url;
ALTER TABLE site CHANGE baseurl base_url;
ALTER TABLE cms CHANGE lastupdate last_update;
ALTER TABLE person ADD last_login datetime;

CREATE TABLE `activity` (
  `id` int(11) NOT NULL auto_increment,
  `site_id` int(11) default 0 NOT NULL,
  `person_id` int(11) default 0 NOT NULL,
  `activity` varchar(255) default NULL,
  `category` varchar(50) default NULL,
  `custom1name` varchar(15) default NULL,
  `custom1val` varchar(50) default NULL,
  `custom2name` varchar(15) default NULL,
  `custom2val` varchar(50) default NULL,
  `created` datetime NOT NULL,
  `ref_url` varchar(500) default NULL,
  `year` int(11) default 1,
  `month` int(11) default 1,
  `day` int(11) default 1,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `helpresponse` (
  `id` int(11) NOT NULL auto_increment,
  `site_id` int(11) default 0 NOT NULL,
  `help_id` int(11) default 0 NOT NULL,
  `person_id` int(11) default 0 NOT NULL,
  `status` int(11) default 1,
  `created` datetime NOT NULL,
  `response` text,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE comment ADD ip varchar(24) default NULL after `blog`;

5/31/08 into prod
CREATE TABLE `help` (
  `id` int(11) NOT NULL auto_increment,
  `site_id` int(11) default NULL,
  `status` int(11) default 1,
  `created` datetime NOT NULL,
  `isuser` tinyint(1) default '0',
  `person_id` int(11) default NULL,
  `ip` varchar(24) default NULL,
  `hashedemail` varchar(32) NOT NULL,
  `url` varchar(255) NOT NULL,
  `blog` varchar(255) default NULL,
  `authorname` varchar(100) default NULL,
  `content` text,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
ALTER TABLE site ADD public tinyint(1) default '0' after `enabled`;
ALTER TABLE site ADD commenturl varchar(255) default '' after `baseurl`;
ALTER TABLE site ADD slug varchar(50) NOT NULL after `name`;
ALTER TABLE help ADD email varchar(150) default NULL after `hashedemail`;


5/20/08: (done into prod)

ALTER TABLE email ADD reply_to varchar(150) default NULL after `to`;
ALTER TABLE site ADD enabled tinyint(1) default '0' after `description`;
ALTER TABLE site ADD description text default NULL after `name`;
ALTER TABLE person ADD issysadmin tinyint(1) default '0' after `isadmin`;
ALTER TABLE comment ADD email varchar(150) default NULL after `hashedemail`;


5/16/08  (done into prod)

ALTER TABLE site ADD baseurl varchar(255) default 'http://localhost:4950/' after `key`;
ALTER TABLE person CHANGE verified verified tinyint(1) default '0' after `waitinglist`;
ALTER TABLE person ADD isadmin tinyint(1) default '0' after `verified`;
ALTER TABLE person ADD authn varchar(8) NOT NULL default 'local' after `user_uniqueid`;
ALTER TABLE person ADD hashedemail varchar(32) default NULL after `authn`;
ALTER TABLE person CHANGE url url varchar(255) default 'http://localhost:4950/';

4/24/08 (done)
CREATE TABLE `comment` (
  `id` int(11) NOT NULL auto_increment,
  `site_id` int(11) default NULL,
  `created` datetime NOT NULL,
  `isuser` tinyint(1) default '0',
  `hashedemail` varchar(32) NOT NULL,
  `type` varchar(50) NOT NULL,
  `uri` varchar(255) NOT NULL,
  `blog` varchar(255) default NULL,
  `authorname` varchar(100) default NULL,
  `comment` text,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

11/10/07

# if doing InnoDB
CREATE TABLE `person_groups` (
  `person_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  KEY `person_id` (`person_id`),
  KEY `group_id` (`group_id`),
  CONSTRAINT `person_groups_fk_groups` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  CONSTRAINT `person_groups_fk_person` FOREIGN KEY (`person_id`) REFERENCES `person` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `groups` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(255) NOT NULL,
  `site_id` int(11) default NULL,
  `group_type` varchar(30) default NULL,
  `created` datetime NOT NULL,
  `description` varchar(500) default NULL,
  `contacts` text,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
ALTER TABLE person CHANGE openidurl url varchar(255);
11/7/07
alter table cms add column content2 text after content;
11/1/07
ALTER TABLE cms ADD rid varchar(255) default null after `key`;
ALTER TABLE cms ADD url varchar(255) after rid;
10/6/07
ALTER TABLE cms ADD children_count int(11) default 1 AFTER site_id;
ALTER TABLE cms ADD lastupdate datetime AFTER children_count;
ALTER TABLE cmslinks DROP children_count;


10/4/07
ALTER TABLE cms ADD item_type varchar(20) default 'cms' AFTER created;

CREATE TABLE `cmslinks` (
  `id` int(11) NOT NULL auto_increment,
  `parent_id` int(11) default NULL,
  `child_id` int(11) default NULL,
  `position` int(11) default '1',
  `children_count` int(11) default '0',
  PRIMARY KEY  (`id`),
  KEY `parent_id` (`parent_id`),
  KEY `child_id` (`child_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;




#
# Earlier
#

CREATE TABLE `cms` (
  `id` int(11) NOT NULL auto_increment,
  `site_id` int(11) default NULL,
  `created` datetime default NULL,
  `title` varchar(120) NOT NULL,
  `key` varchar(150) NOT NULL,
  `content` text,
  `tags` varchar(500) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# Structure for the `site` table : 
#

CREATE TABLE `site` (
  `id` int(11) NOT NULL auto_increment,
  `library_id` int(11) default NULL,
  `email` varchar(255) default NULL,
  `name` varchar(255) default NULL,
  `key` varchar(50) default NULL,
  `created` datetime default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# Structure for the `email` table : 
#

CREATE TABLE `email` (
  `id` int(11) NOT NULL auto_increment,
  `site_id` int(11) default NULL,
  `key` varchar(150) NOT NULL,
  `subject` varchar(120) NOT NULL,
  `from_email` varchar(150) NOT NULL,
  `from_name` varchar(120) default NULL,
  `to` varchar(1000) NOT NULL,
  `template` text,
  `created` datetime default NULL,
  PRIMARY KEY  (`id`),
  KEY `site_id` (`site_id`),
  CONSTRAINT `email_ibfk_1` FOREIGN KEY (`site_id`) REFERENCES `site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# Structure for the `person` table : 
#

CREATE TABLE `person` (
  `id` int(11) NOT NULL auto_increment,
  `site_id` int(11) NOT NULL,
  `email` varchar(255) default NULL,
  `displayname` varchar(50) default NULL,
  `created` datetime default NULL,
  `waitinglist` int(11) NOT NULL,
  `user_uniqueid` varchar(40) default NULL,
  `random_salt` varchar(40) default NULL,
  `hashed_password` varchar(120) default NULL,
  `openidurl` varchar(255) default NULL,
  `verified` tinyint(1) default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_uniqueid` (`user_uniqueid`),
  KEY `site_id` (`site_id`),
  CONSTRAINT `person_fk_site` FOREIGN KEY (`site_id`) REFERENCES `site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
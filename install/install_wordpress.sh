#!/usr/bin/env bash
# 
#  chmod +x install_wordpress.sh mysql_root_pwd wp_mysql_pwd
# ----------------------------------------------------------------------------
#  TODO
#   - 
# ----------------------------------------------------------------------------
function die
{
    echo $*
    exit 1
}
function checkRoot
{
    if [ ! $( id -u ) -eq 0 ]; then
        die "Must have super-user rights to run this script.  Run with the command 'sudo $0'"
    fi
}
# Get all arguments if not supplied
function askArgs
{
      echo -en "Please enter your MySQL root password: or 
  return to accept [demisauce]"
      read MYSQL_ROOT_PWD
      if [ "$MYSQL_ROOT_PWD" = "" ] ; then
          MYSQL_ROOT_PWD="demisauce"
      fi
      echo -en "Please enter password for the MySQL password for the wordpress web app or
  return to accept [demisauce]"
      read DEMISAUCE_MYSQL_PWD
      if [ "$DEMISAUCE_MYSQL_PWD" = "" ] ; then
          DEMISAUCE_MYSQL_PWD="demisauce"
      fi
}

#------- Start of program
DEMISAUCE_HOME='/home/demisauce'
SERVER_ROLE='all'
#DEMISAUCE_MYSQL_PWD='demisauce'
#MYSQL_ROOT_PWD='demisauce'

checkRoot
if [ $# -eq "0" ] ; then
    askArgs
else 
    MYSQL_ROOT_PWD=$1
    DEMISAUCE_MYSQL_PWD=$2
fi




echo "----  adding memcached extension to php  /etc/php5/apache2/php.ini "
#  Adds this:    extension=memcache.so    
perl -pi -e s/\;\ extension_dir\ directive\ above./\;\ extension_dir\ directive\ above.\\nextension=memcache.so/g /etc/php5/apache2/php.ini || die "Could not update php.ini"

cd /var/www
wget http://wordpress.org/latest.tar.gz
tar -xzvf latest.tar.gz  
rm latest.tar.gz
mv -f wordpress blog
cat <<EOL > wordpress.sql
create database if not exists wordpress DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;
use mysql;
GRANT ALL PRIVILEGES ON wordpress.* TO 'ds_web'@'localhost' IDENTIFIED BY '$DEMISAUCE_MYSQL_PWD' WITH GRANT OPTION;
flush privileges;
EOL
mysql -uroot -p$MYSQL_ROOT_PWD < wordpress.sql || die "Could not set up database for Demisauce."
rm -f wordpress.sql

# get WP UniqueKeys
WPKEYS="$(wget -o/dev/null -O- http://api.wordpress.org/secret-key/1.1/)"
cat <<EOL > wordpress/wp-config.php
<?php
/** 
 * The base configurations of the WordPress.
 *
 * This file has the following configurations: MySQL settings, Table Prefix,
 * Secret Keys, WordPress Language, and ABSPATH. You can find more information by
 * visiting {@link http://codex.wordpress.org/Editing_wp-config.php Editing
 * wp-config.php} Codex page. You can get the MySQL settings from your web host.
 *
 * This file is used by the wp-config.php creation script during the
 * installation. You don't have to use the web site, you can just copy this file
 * to "wp-config.php" and fill in the values.
 *
 * @package WordPress
 */

// ** MySQL settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define('DB_NAME', 'wordpress');
/** MySQL database username */
define('DB_USER', 'ds_web');

/** MySQL database password */
define('DB_PASSWORD', '$DEMISAUCE_MYSQL_PWD');

/** MySQL hostname */
define('DB_HOST', 'localhost');

/** Database Charset to use in creating database tables. */
define('DB_CHARSET', 'utf8');

/** The Database Collate type. Don't change this if in doubt. */
define('DB_COLLATE', '');

/**#@+
 * Authentication Unique Keys.
 *
 * Change these to different unique phrases!
 * You can generate these using the {@link http://api.wordpress.org/secret-key/1.1/ WordPress.org secret-key service}
 *
 * @since 2.6.0
 */
$WPKEYS
/**#@-*/

/**
 * WordPress Database Table prefix.
 *
 * You can have multiple installations in one database if you give each a unique
 * prefix. Only numbers, letters, and underscores please!
 */
\$table_prefix  = 'wp_';

/**
 * WordPress Localized Language, defaults to English.
 *
 * Change this to localize WordPress.  A corresponding MO file for the chosen
 * language must be installed to wp-content/languages. For example, install
 * de.mo to wp-content/languages and set WPLANG to 'de' to enable German
 * language support.
 */
define ('WPLANG', '');

/* That's all, stop editing! Happy blogging. */

/** WordPress absolute path to the Wordpress directory. */
if ( !defined('ABSPATH') )
	define('ABSPATH', dirname(__FILE__) . '/');

/** Sets up WordPress vars and included files. */
require_once(ABSPATH . 'wp-settings.php');
?>
EOL
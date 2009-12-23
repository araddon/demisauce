
CFG = {
    'demisauce_appname':'app',
    'demisauce_url':'http://www.demisauce.com',
    'demisauce_api_key':'bogus',
    'memcache_servers':'127.0.0.1:11211,localhost:11211',
    'gearman_servers':'localhost',
    'email_from': 'fake@fake.com',
    'email_from_name': "Demisauce Admin",
    'smtp_username':"demisauce@demisauce.org",
    'smtp_password':"pwd",
    'smtp_server':"mockserver.com",
}
SERVER = 'http://localhost:4950'

def show():
    print('cfg.py CFG = %s' % (CFG))


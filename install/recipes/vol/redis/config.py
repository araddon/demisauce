import os

#DATA_DIR = os.path.join(os.path.realpath(os.path.curdir), "data")
#cur_dir = os.path.dirname(os.path.realpath(__file__))
cur_dir = os.path.realpath(os.path.curdir)
print("Current Directory = %s" % cur_dir)
DATA_DIR = os.path.realpath(cur_dir + '/install/recipes/vol/redis/data' )

USE_MASTER = True
DEBUG = False

NODES = {
    #Lookup nodes
    'lookup1_AM': { 'id': 1, 'host': '192.168.0.112:6379', 'master': None },

    #Storage nodes
    'storage1_BM': { 'id': 11, 'host': '192.168.0.112:6379', 'master': None },
}



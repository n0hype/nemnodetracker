import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    '''
    front end config
    '''
    GRAPH_COLORS = ['rgb(57,106,177)','rgb(218,124,48)','rgb(62,150,81)','rgb(204,37,41)','rgb(83,81,84)','rgb(107,76,154)','rgb(146,36,40)','rgb(148,139,61)']

    '''
    updateNodeState config

    trusted nodes to be  uses as seed/dafault/most trusted/lowest ping nodes
    all block chain related requests will be sent primarily to  DEFAULT_CLIENT
    this should be your own node

    if DEFAULT_CLIENT fails to respond, request will be sent to random node with importance above NODE_IMPORTANCE_TRESHOLD
    0.0003 will get you only and most of supernodes, which we have plenty of right now

    during first run of this script, there are no nodes in db to chose from.
    SEED_NODES are added to db before any requests are made.
    WARNING: if your SEED_NODES are below NODE_IMPORTANCE_TRESHOLD they will not be used!
    '''
    DEFAULT_CLIENT = 'http://192.168.1.10:7890'
    SEED_NODES = ['http://45.76.178.172:7890','http://45.63.107.13:7890','http://62.113.207.190:7890']
    NODE_IMPORTANCE_TRESHOLD = 0.0003
    REQUEST_TIMEOUT = 3

    '''
    updateBlockHeightState config:

    we determine bolck height of main chain by asking trusted nodes for their height.
    if consensus about certain height reaches BLOCK_HEIGHT_ACCEPT_TRESHOLD we consider it bolck height of main chain.
    if consensus does not reach BLOCK_HEIGHT_ACCEPT_TRESHOLD, we wait SLEEP_BETWEEN_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD
    and try again - maximum MAX_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD before raising exception

    average block time on NEM chain is 1 minute. there are some blocks with as low as 15sec creation time.
    it takes us REQUEST_TIMEOUT + ~ 1 seconds to get block_height of each node
    during this time network can be in transition state between 'main height' and 'main height'-1
    hence SLEEP_BETWEEN_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD

    for the purpose of this script it should be safe to use low value of BLOCK_HEIGHT_ACCEPT_TRESHOLD,
    however setting low BLOCK_HEIGHT_ACCEPT_TRESHOLD will result in many nodes being on 'main height'-1 many times.
    this shell not be forgoten while interpreting final data.

    setting high BLOCK_HEIGHT_ACCEPT_TRESHOLD and
    low SLEEP_BETWEEN_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD and MAX_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD
    may cause script to rarely converge ...

    every node with importance over NODE_IMPORTANCE_TRESHOLD is considered 'trusted node'
    in good times NODE_IMPORTANCE_TRESHOLD could be set to None, but why not use it, when we have it?
    (see above)
    '''
    BLOCK_HEIGHT_ACCEPT_TRESHOLD = 0.6
    MAX_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD = 5
    SLEEP_BETWEEN_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD = 5
    ASYNC_REQUEST_TIMEOUT = 10

'''
communication with NEM infrastructure server (nis)
https://nemproject.github.io/
doing some formating
'''
import requests

import json

from functools import wraps
import time
from random import choice

def requestHandler(func):
    '''
    INPUT:
    :func: func dealing with request and response.json() unpacking

    this decorator converts all possible errors of response.json()[]... to None with som basic logging

    OUTPUT:
    if everything ok: func return
    if not: None
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):

        endpoint = args[0].endpoint
        print(f'sending {func.__name__} request to {endpoint}')
        try:
            result = func(*args, **kwargs)
            print(f'response OK')
        except requests.exceptions.RequestException as e:
            result = None
            print(f'response NOK')
            print(e)
        except KeyError as e:
            #sometimes node sends <response 200> but resulting .json() data are not correct
            #this probabbly should not happen??
            result = None
            print(f'response NOK')
            print(f'KeyError - reason {str(e)}')
        except:
            result = None
            print('response NOK')
            print('unknown error')
        return result

    return wrapper

class nemConnect():
    def __init__(self, default_client_endpoint, timeout=1, client_endpoint_list=[]):
        """
        Initialize client.
        :param endpoint: address of the NIS. 'http://85.216.239.0:7890'
        :param timeout: integer requests timeout
        :param client_endpoint_list: list of clients endpoints ['http://85.216.239.0:7890', 'http://99.99.99.9:7890']
        """
        self.default_endpoint = default_client_endpoint
        self.endpoint = self.default_endpoint
        self.timeout = timeout
        self.session = requests.Session()
        self.endpoint_list = client_endpoint_list

    def sendGet(self, callName, data):
        ''' generate get request object and return response object'''
        headers = {'Content-type': 'application/json'}
        uri = self.endpoint + '/' + callName
        return self.session.get(uri, params=data, headers=headers, timeout=self.timeout)

    # simple requests
    @requestHandler
    def getNodePubKey(self):
        '''
        get pub_key of nis(self.endpoint) from nis(self.endpoint)
        OUTPUT pub_key as string
        '''
        r = self.sendGet('node/info', None)
        return r.json()['identity']['public-key']

    @requestHandler
    def getReachableNodes(self):
        '''
        get reachable nodes(other nis on internet) from nis(self.endpoint)
        OUTPUT list of data json structures
        will be used in getReachableNodesSet()
        '''
        r = self.sendGet('node/peer-list/reachable', None)
        return r.json()['data']

    @requestHandler
    def getImportanceOfPubKey(self, pub_key):
        '''
        get importance of accout with corresponding pub_key
        or importance of account which delegated its importance to accout with corresponding pub_key
        from nis(self.endpoint)

        OUTPUT: importance as integer
        '''
        data = {'publicKey':pub_key}
        r = self.sendGet('account/get/forwarded/from-public-key', data)
        return r.json()['account']['importance']

    @requestHandler
    def getChainHeight(self):
        '''
        get chain height of nis(self.endpoint) from nis(self.endpoint)
        OUTPUT: chain height as integer
        '''
        r = self.sendGet('chain/height', None)
        return r.json()['height']

    @requestHandler
    def getChainScore(self):
        '''
        get chain score of nis(self.endpoint) from nis(self.endpoint)
        OUTPUT: chain score as integer
        '''
        r = self.sendGet('chain/score', None)
        return int(r.json()['score'],16)

    @requestHandler
    def getNodeState(self):
        '''
        get status of nis(self.endpoint) from nis(self.endpoint)
        OUTPUT: status code as integer

        nis states:
            0: Unknown status.
            1: NIS is stopped.
            2: NIS is starting.
            3: NIS is running.
            4: NIS is booting the local node (implies NIS is running).
            5: The local node is booted (implies NIS is running).
            6: The local node is synchronized (implies NIS is running and the local node is booted).
            7: NIS local node does not see any remote NIS node (implies running and booted).
            8: NIS is currently loading the block chain from the database. In this state NIS cannot serve any requests.
        '''
        r = self.sendGet('status', None)
        return r.json()['code']

    # composite requests
    def getReachableNodesSet(self):
        '''
        get reachable nodes(other nis on internet) from nis(self.endpoint)
        OUTPUT set of tuples (pub_key, endpoint)
        '''
        result = set()

        reachable_nodes = self.getReachableNodes()

        if reachable_nodes is None:
            reachable_nodes = []

        for item in reachable_nodes:
            pub_key = item['identity']['public-key']
            name = item['identity']['name']
            endpoint = str(item['endpoint']['protocol']) + '://' + str(item['endpoint']['host']) + ':' + str(item['endpoint']['port'])
            # result.add(db.Node(pub_key=pub_key, endpoint=endpoint, active=True))
            result.add((pub_key, endpoint, name, True))

        return result

    def getBlockHeightAndScore(self):
        '''
        get chain score,chain height of nis(self.endpoint) from nis(self.endpoint)
        OUTPUT: chain score, chain height as integers
        '''
        return  self.getChainHeight(), self.getChainScore()

    def getImportanceOfPubKeyNodePool(self, pub_key):
        kill_switch = 0
        importance = None
        self.endpoint = self.default_endpoint
        while importance == None:
            # try to get response from client node
            importance = self.getImportanceOfPubKey(pub_key)
            # if response from default node is NOK and we have no high importance nodes in db to contact
            if importance is None and not self.endpoint_list:
                # some times we are just sending too many requests too fast and trigger some dos protection on node
                # with nem node on local network and default settings this happens every few requests
                time.sleep(0.5)
                kill_switch += 1
            # if response from default node is NOK, but we have other high importance Nodes
            # -> change cliet to different node
            elif importance is None and self.endpoint_list:
                self.endpoint = choice(self.endpoint_list)
                kill_switch += 1
            # if importance is not None -> everything OK!

            if kill_switch > 20:
                raise Exception('Could not contact DEFAULT_CLIENT nor any of 20 random nodes! Check you connection.'
                    ' If this is the first run of this script insert some nodes to SEED_NODES')
                return None

        return importance

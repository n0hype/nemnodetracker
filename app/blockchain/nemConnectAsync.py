'''
communication with NEM infrastructure servers (nis) asynchronously using pool of nis-es
https://nemproject.github.io/
doing some formating
'''

import grequests
import json
from datetime import datetime

class nemConnectAsync():
    def __init__(self, timeout=1):
        """
        Initialize client.
        :param timeout: requests timeout
        """
        self.timeout = timeout

    def sendGet(self, callName, endpoint, data):
        ''' generate gerquest get request object '''
        headers = {'Content-type': 'application/json'}
        uri = endpoint + '/' + callName
        return grequests.get(uri, params=data, headers=headers, timeout=self.timeout)

    def responseReslover(self, response_list, arg):
        '''
        INPUT:
        :param response_list: grequests response objects
        :arg: key of dict of response.json() scructure

        this function converts all NotOK responses to None and all OK responses to desired value
        no logging, this has to be super fast

        OUTPUT:
        if everything ok : desired value
        if not: None
        '''
        # could be used in future for more robustness with *args
        # call = 'r.json()'
        # for arg in args:
        #     call += f'[{repr(arg)}]'
        call = f'r.json()[{repr(arg)}]'
        result = []
        for r in response_list:
            try:
                result.append(eval(call))
            except:
                result.append(None)
        return result

    def getHeightOfEachNode(self, endpoint_list):
        '''
        :param endpoint_list: list of 'http://85.216.239.0:7890'
        get block height of each node in node_list asynchronously

        OUTPUT: list of block heights on Nones
        '''
        reqs = [self.sendGet('chain/height', e, None) for e in endpoint_list]

        time_stamp = datetime.utcnow()
        responses = grequests.map(reqs)

        return self.responseReslover(responses, 'height'), time_stamp

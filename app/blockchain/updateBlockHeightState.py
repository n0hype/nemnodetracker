'''
idea of this script is to each time:
    determine bolck height of main chain
    save relative height of tracked nodes
    save overall statistics about heights of nodes in network

see config.py for more info abou config values
'''
#app imports
from app import app, db
from app.models import Node, BlockHeight, ChainState

#my imports
from app.blockchain.nemConnectAsync import nemConnectAsync

# other imports
from collections import Counter
from time import sleep
import json

#config
NODE_IMPORTANCE_TRESHOLD = app.config['NODE_IMPORTANCE_TRESHOLD']
BLOCK_HEIGHT_ACCEPT_TRESHOLD = app.config['BLOCK_HEIGHT_ACCEPT_TRESHOLD']
MAX_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD = app.config['MAX_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD']
SLEEP_BETWEEN_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD = app.config['SLEEP_BETWEEN_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD']
ASYNC_REQUEST_TIMEOUT = app.config['ASYNC_REQUEST_TIMEOUT']

#nemConnect setup
nis = nemConnectAsync(ASYNC_REQUEST_TIMEOUT)

def dbGetActiveNodes(node_importance_treshold):
    # get all active nodes from db ordered by importance decresing
    q = db.session.query(Node.id, Node.endpoint, Node.track_block_height)\
        .filter(Node.active == True)\
        .order_by(Node.importance.desc())\
        .all()
    # get how many nodes are with importance over node_importance_treshold -> will be used as trusted nodes
    if node_importance_treshold:
        trusted_height_count = db.session.query(db.func.count(Node.id))\
            .filter(Node.active == True, Node.importance > node_importance_treshold)\
            .one()[0]
    else:
        trusted_height_count = db.session.query(db.func.count(Node.id))\
            .filter(Node.active == True)\
            .one()[0]
    # unzip data from query
        #   id_list - list of ids of each node in db
        #   endpoint_list - list og endpoints of each node
        #   track_block_height - list of True/False - if block height of that node should be recorded to db at the end of this excesise
    # this script should be run every 1-10 minutes for years to come ..
    # it is impossible in future we will ask money for node to be added to track_block_height
    id_list, endpoint_list, track_block_height = zip(*q)

    # each of this lists will be used separatelly and than zipped back together
    # trusted_height_count is count of nodes with importance above NODE_IMPORTANCE_TRESHOLD
    return id_list, endpoint_list, track_block_height, trusted_height_count

def dbUpdateChainState(id_list, endpoint_list, height_list, track_block_height, time_stamp):

    # get data for ChainState table
    timeout_count = len([h for h in height_list if h is None])
    # get height distribution of all nodes
    height_distribution = Counter(height_list).most_common()
    # get most common block height
    # height distribution can be [] - empty list
    if height_distribution:
        most_common_height, most_common_count = height_distribution[0]
        # None can be most common block height, if many nodes dont respond
        if most_common_height is None:
            most_common_height, most_common_count = height_distribution[1]
    else:
        most_common_height, most_common_count = 0, 0

    # create new ChainState
    chain_state = ChainState(time=time_stamp, most_common_height=most_common_height, most_common_count=most_common_count,\
                                height_distribution=json.dumps(height_distribution), timeout_count=timeout_count,\
                                nodes_tested=len(id_list))

    # get list of (node_id,block_height) for all tracked nodes (see Node.track_block_height)
    nodes_to_track = [(row[0],row[1]) for row in zip(id_list,height_list,track_block_height) if row[2]]
    # append block_height of each node to current chain_state
    for id, height in nodes_to_track:
        if height is not None:
            relative_height = height - most_common_height
        else:
            relative_height = None
        chain_state.block_height.append(BlockHeight(node_id=id, relative_height=relative_height))

    # add chain_state and all block_heights append to it to db.session
    db.session.add(chain_state)
    db.session.commit()

# this function reads REQUEST_TIMEOUT, but only for logging
def blockHeightAcceptCondition(ok_nodes_count, trusted_nodes_count, treshold, max_tryes):
    print(f'try {blockHeightAcceptCondition.counter}, nodes in sync {ok_nodes_count *100 / trusted_nodes_count}%, {treshold*100}% needed')

    blockHeightAcceptCondition.counter += 1
    if blockHeightAcceptCondition.counter <=  max_tryes:
        return ok_nodes_count / trusted_nodes_count > treshold
    else:
        raise Exception('Max tryes for block height sync reached, '
            f'increase REQUEST_TIMEOUT(={ASYNC_REQUEST_TIMEOUT}) or '
            f'MAX_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD(={max_tryes}) or '
            f'decrease BLOCK_HEIGHT_ACCEPT_TRESHOLD(={treshold})')

def main():
    # get ordered lists of data corresponding to each node (every active node in Nodes table )
    # each of this lists will be used separatelly and than zipped back together
    # trusted_height_count is count of nodes with importance above NODE_IMPORTANCE_TRESHOLD
    # check dbGetActiveNodes() for more info
    id_list, endpoint_list, track_block_height, trusted_height_count = dbGetActiveNodes(NODE_IMPORTANCE_TRESHOLD)

    # most_common_count is number of nodes that are on most prevelant block height
    # we get this count by asking only trusted nodes for bock height
    most_common_count, blockHeightAcceptCondition.counter = 0, 0

    # start of network block height convergence procedure
    while not blockHeightAcceptCondition(
                            most_common_count, trusted_height_count,
                            BLOCK_HEIGHT_ACCEPT_TRESHOLD,
                            MAX_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD):
        if  blockHeightAcceptCondition.counter > 1:
            print('sleeping')
            sleep(SLEEP_BETWEEN_TRYES_TO_REACH_BLOCK_HEIGHT_ACCEPT_TRESHOLD)

        # get height of each node asynchronously and
        # time_stamp right before grequests.map() -> start of sending requests to nodes
        height_list, time_stamp = nis.getHeightOfEachNode(endpoint_list)

        print(f'height_distribution: {Counter(height_list).most_common()}')
        # height_list contains height, if everything OK or None if anything wrong
        # trust_height is ordered list of True/False
        trust_height = [True if i<trusted_height_count else False for i in range(len(id_list))]
        trusted_height_list_no_Nones = [row[0] for row in zip(height_list,trust_height) if row[0] and row[1]]
        # get distribution of heights of trusted nodes
        truested_height_distribution = Counter(trusted_height_list_no_Nones).most_common()
        # get most common block height and noumber of nodes whit that height
        # -> will determine if that block_height will be considered block height of network
        if truested_height_distribution:
            most_common_height, most_common_count = truested_height_distribution[0]
        else:
            most_common_height, most_common_count = 0, 0

    dbUpdateChainState(id_list, endpoint_list, height_list, track_block_height, time_stamp)


if __name__ == '__main__':
    main()

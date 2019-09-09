'''
construct and update list of reachable nodes stored in our db
see config.py for more info abou config values
'''

# app and db imports
from app import app, db
from app.models import Node, NodeState

#my imports
from app.blockchain.nemConnect import nemConnect

# other imports
from random import shuffle
from datetime import datetime

#config - see config.py
DEFAULT_CLIENT = app.config['DEFAULT_CLIENT']
NODE_IMPORTANCE_TRESHOLD = app.config['NODE_IMPORTANCE_TRESHOLD']
SEED_NODES = app.config['SEED_NODES']
REQUEST_TIMEOUT = app.config['REQUEST_TIMEOUT']


def dbInsertSeedNodes(seed_nodes):
    '''
    if Node table is empty -> insert nodes from seed_nodes
    these nodes are used as backup if default_cliet is not answering
    '''
    db_node_list = db.session.query(Node).filter_by(active=True).all()
    # if no nodes in db -> add nodes from default_client_list
    if db_node_list == []:
        for endpoint in seed_nodes:
            # request pub_key from that node
            nis = nemConnect(endpoint,REQUEST_TIMEOUT)
            pub_key = nis.getNodePubKey()
            importance = nis.getImportanceOfPubKey(pub_key)
            # if node responds with pub_key it is added to db as active
            if pub_key is not None:
                active = 1
                db.session.add(Node(pub_key=pub_key, endpoint=endpoint, active=active, importance=importance))
            db.session.flush()
        db.session.commit()

def node_obj_to_tupl(node_obj_list):
    '''
    convert list of Node objects     Node(pub_key=pub_key, endpoint=endpoint, active=active)
    to set of tuples                            (pub_key, endpoint, True)
    '''
    result = set()
    for item in node_obj_list:
        result.add((item.pub_key, item.endpoint, item.name, item.active))
    return result

def db_update_node_list(nis_reachable_nodes, nis):
    '''
    INPUT:
    :param nis_reachable_nodes: set of tubles (pub_key, endpoint, name, active) (from nemConnect.getReachableNodes())
    :db:                        list of all Nodes
    :nemConnect:                .getImportanceOfPubKeyNodePool
    OUTPUT: updates list of nodes in db

    Purpose of this function is only to add new nodes, activate inactive nodes and deactivate node,
    when other node with either tahe same pub_key or same endpoint apperars.
    There will be other mechanism to deactivate nodes for inactivity.

    Some thoughts on this function ....

    record = combination of (pub_key, endpoint, name, active), properties of Node
    constraints:
        it is impossible to have 2 nodes with 2 pub_keys on single endpoint

    scenarios:
        1. high importance node changes ip (ip never used by any node) -> endpoint is updated in corresponding db record
        2. 0 importance node changes ip (ip never used by any node)-> endpoint is updated in corresponding db record
        3. 0 importance node is rebooted with new pub_key -> pub_key is updated in corresponding db record
        4. node changes name -> name is updated in corresponding db record
        5. previously deactivated node is now active -> activate bit is updated in corresponding db record
        6. multiple nodes are booted with same pub_key
            -> let them live = PUB KEY IS NOT UNIQUE IN DB
                = way too dificult to implement, noone is doing this currently and it should not be done in my opinion
            -> reduce them to one record without special care = same as 1,2 = PUB KEY IS UNIQUE IN DB
            {This should be mentioned in explanation of final data}
        7. node with already recorded pub_key changes endpoint to endpoint of different already recorded node -> is this life?
            -> pub_key wins, new node gets endpoint, old node is deactivated = ENDPOINT IS NOT UNIQUE IN DB
        8. sb has multiple high importance nodes and shuffles their endpoints/pub_keys
            -> if we evaluate one record at the time this is reduced to 7
        9. new node added to network -> add to db

    not to forget:
        endpoint uniquesness between active nodes has to be ensured while in all records endpoint is not unique
        pub keys are uique in db

    FLOW CHART:
        get records from nis api, and db

        if the record from nis api is the same as record in db it is droped
        from now on every record is update or new insert

        if pub_key in db:
            if endpoint in same record = scenarion(4,5)-> update name and active=True
            if not = s(1,2,6,7,8) -> update endpoint - BUT endpoint of active nodes has to be unique ->
                if endpoint not in different active record = s(1,2,6) ->  update endpoint
                if endpoint in different active record = s(7,8) -> update endpoint, deactivate other record

        if pub_key not in db s(3,9):
            if pub key high importance = will be treated as new node:
                if endpoint in different active record -> new record, deactivate old record
                if endpoint not in different active record -> new record
            if pub key 0 importance = will be treated as reboot of existing node:
                if endpoint in different record with 0 importance:
                    update only 0 importance record preferably active
                else = (9) -> new record

    '''
    # filter out records from nem api that are already in db
    db_node_dump = db.session.query(Node).all()
    nis_reachable_nodes_update = nis_reachable_nodes - node_obj_to_tupl(db_node_dump)

    # set up nemConnect


    for pub_key,endpoint,name,active in nis_reachable_nodes_update:
        # if pub_key in db: update endpoint in db record. endpoint in all active nodes in db must be unique!
        # in other functions we will be sending http requests to all active nodes.
        to_update_db_record = db.session.query(Node).filter(Node.pub_key == pub_key).one_or_none()
        if to_update_db_record:
            # if pub_key and endpoint in same db record -> update name or activate
            if endpoint == to_update_db_record.endpoint:
                to_update_db_record.name, to_update_db_record.active = name, True
            # if endpoint different in db record -> update endpoint
            # BUT endpoint in all active nodes in db must be unique!
            else:
                # deactivate all other active records with same endpoint
                db.session.query(Node).filter(Node.endpoint == endpoint, Node.active == True).update({"active": False})
                to_update_db_record.endpoint = endpoint
                # name and activity could also be different
                to_update_db_record.name, to_update_db_record.active = name, True
        #if pub_key not in db
        else:
            importance = nis.getImportanceOfPubKeyNodePool(pub_key)
            # if pub key high importance = will be treated as new node
            if importance > 0.0:
                # deactivate all other active records with same endpoint
                db.session.query(Node).filter(Node.endpoint == endpoint, Node.active == True).update({"active": False})
                db.session.add(Node(pub_key=pub_key, endpoint=endpoint, name=name, active=True, importance=importance))

            # if pub key 0 importance = will be treated as reboot of existing node:
            else:
                # if endpoint in different record with 0 importance:
                # update only 0 importance record preferably active
                to_update_db_record = db.session.query(Node)\
                    .filter(Node.endpoint == endpoint, Node.importance == 0.0)\
                    .order_by(Node.active)\
                    .first()
                if to_update_db_record:
                    to_update_db_record.pub_key = pub_key
                    # name and activity could also be different
                    to_update_db_record.name, to_update_db_record.active = name, True
                else:
                    # deactivate all other active records with same endpoint
                    db.session.query(Node).filter(Node.endpoint == endpoint, Node.active == True).update({"active": False})
                    db.session.add(Node(pub_key=pub_key, endpoint=endpoint, name=name, active=True, importance=importance))
        db.session.flush()

    db.session.commit()

def dbUpdateNodesImportance(nis):
    node_list = db.session.query(Node).filter_by(active=True).all()
    # get top importance nodes from db, only nodes with importance over NODE_IMPORTANCE_TRESHOLD will be picked
    # will be used as back up nodes to contact if DEFAULT_CLIENT fails
    for node in node_list:
        importance = nis.getImportanceOfPubKeyNodePool(node.pub_key)

        # update importance of node only if it is not None or 0.0
        # importance = Column(Float(precision=32), default=0.0) - 0.0 is already in db
        if importance:
            node.importance = importance
        db.session.flush()
    db.session.commit()


def dbUpdateNodeState():
    no_importance_nodes_online = db.session.query(db.func.count(Node.id))\
        .filter(Node.active == True, Node.importance == 0.0)\
        .one()[0]
    high_importance_nodes_online = db.session.query(db.func.count(Node.id))\
        .filter(Node.active == True, Node.importance > 0.0)\
        .one()[0]
    booted_importance_sum = db.session.query(db.func.sum(Node.importance))\
        .filter(Node.active == True)\
        .one()[0]
    time_stamp = datetime.utcnow()

    db.session.add(NodeState(time=time_stamp, no_importance_nodes_online=no_importance_nodes_online,
        high_importance_nodes_online=high_importance_nodes_online,
        booted_importance_sum=booted_importance_sum))

    db.session.commit()

def dbGetRandomNodes(importance_treshold):
    '''
    input:  Node table from db
    :param importance_treshold: float, will chose only from nodes with importance above limit,
                                if None, will chose from all nodes
    output:
    random list of endpoints of nodes with importance above importance_treshold
    '''
    # this query returns list of tuples [('http://107.191.50.14:7890'), ('http://45.76.178.172:7890')]
    if importance_treshold is None:
        query = db.session.query(Node.endpoint)\
            .filter(Node.active == True)\
            .all()
    else:
        query = db.session.query(Node.endpoint)\
            .filter(Node.active == True, Node.importance > importance_treshold)\
            .all()

    # shuffle list of endpoints to pick from
    shuffle(query)

    # return format ['http://107.191.50.14:7890', 'http://45.76.178.172:7890']
    return [record[0] for record in query]

def main():
    # first run setup: if Node table is empty -> insert nodes from SEED_NODES
    dbInsertSeedNodes(SEED_NODES)

    # set up nemConnect with DEFAULT_CLIENT and random_client_list from db as node pool
    random_client_list = dbGetRandomNodes(NODE_IMPORTANCE_TRESHOLD)
    nis = nemConnect(DEFAULT_CLIENT, REQUEST_TIMEOUT, random_client_list)

    # check (and update db) for reachable nodes as seen by DEFAULT_CLIENT and some random nodes
    # take 3 random nodes out of nodes with importance over NODE_IMPORTANCE_TRESHOLD from db (Node)
    for endpoint in [DEFAULT_CLIENT] + random_client_list[0:3]:
        nis_reachable_nodes = nemConnect(endpoint,REQUEST_TIMEOUT).getReachableNodesSet()
        db_update_node_list(nis_reachable_nodes, nis)

    # update node importances according to chain on DEFAULT_CLIENT
    # if DEFAULT_CLIENT is not answering use some other from random_client_list
    # takes long time. 99% is waiting for request from node
    dbUpdateNodesImportance(nis)

    # add new record to NodeState table
    dbUpdateNodeState()

if __name__ == '__main__':
    main()

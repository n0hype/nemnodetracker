# sqlalchemy and db imports

from app import db, cache

from app.models import Node, BlockHeight, ChainState, NodeState
from sqlalchemy.orm import joinedload, contains_eager


from itertools import groupby
from operator import itemgetter
from collections import Counter
import json



# node1 = session.query(db.Node).filter(db.Node.active == True).order_by(db.Node.importance.desc()).first()
# print(node1.BlockHeight[0].ChainState)

def data():
    #q = session.query(Node).filter(Node.active == True).order_by(Node.importance.desc()).all()
    q = (session.query(Node.endpoint, BlockHeight.relative_height, ChainState.time)
        .filter(Node.id == BlockHeight.node_id)
        .filter(BlockHeight.ChainState_id == ChainState.id)
        .filter(Node.active == True)
        .order_by(Node.id.desc(), ChainState.time.asc())
        .all())





    datasets = []
    labels, values = [], []

    for k,g in groupby(q, key=itemgetter(0)):
        datasets.append(k)
        points = ([(row[2],row[1]) for row in g])
        l, v = zip(*points)
        labels.append(l)
        values.append(v)



    return datasets[0], list(labels[0]), list(values[0])


@cache.cached(timeout=6000, key_prefix='getNodeState')
def getNodeState():
    q = (db.session.query(NodeState)
        .order_by(NodeState.time.asc())
        .all())

    times = []
    no_importance_nodes_online, high_importance_nodes_online, booted_importance_sum = [], [], []

    for row in q:
        times.append(row.time.isoformat())
        no_importance_nodes_online.append(row.no_importance_nodes_online)
        high_importance_nodes_online.append(row.high_importance_nodes_online)
        booted_importance_sum.append(row.booted_importance_sum)

    no_importance_nodes_online = json.dumps(no_importance_nodes_online)
    high_importance_nodes_online = json.dumps(high_importance_nodes_online)
    booted_importance_sum = json.dumps(booted_importance_sum)

    return (times, no_importance_nodes_online, high_importance_nodes_online, booted_importance_sum)


@cache.cached(timeout=600, key_prefix='getNodesHeights')
def getNodesHeights():
    q = (db.session.query(ChainState)
        .options(joinedload(BlockHeight, BlockHeight.chain_state_id == ChainState.id))
        .options(joinedload(Node, Node.id == BlockHeight.node_id))
        .order_by(ChainState.time.asc())
        .all())

    times = []
    results = {}

    #results['cobalt'] = []
    for i,chain_state in enumerate(q):
        times.append(chain_state.time.isoformat())
        for block_height in chain_state.block_height:
            if block_height.node.name not in results:
                results[block_height.node.name] = [] + [None] * i
            # if block_height.relative_height is not None:
            #     results[block_height.node.name].append(block_height.relative_height + chain_state.most_common_height)
            # else:
            #     results[block_height.node.name].append(None)
            results[block_height.node.name].append(block_height.relative_height)
    for key in results.keys():
        results[key] = json.dumps(results[key])
    return (times, list(results.items()))

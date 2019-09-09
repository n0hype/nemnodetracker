'''
script to set nodes for tracking in Block_height table by setting Node.track_block_height to True
note that node has to be Node.active == True in order to be used in first place
in future this might scan donation address for donations and activate accordingly
'''

from app import db, app
from app.models import Node

NODES_TO_TRACK = app.config['NODES_TO_TRACK']

def activateTopImportanceNodes(no_of_nodes_to_track):
    nodes_to_track = Node.query\
                        .filter(Node.active == True)\
                        .order_by(Node.importance.desc())\
                        .slice(0,no_of_nodes_to_track).all()
    for node in nodes_to_track:
        node.track_block_height = True

    db.session.commit()

def activate():
    nodes_to_track_input_list = NODES_TO_TRACK
    nodes_to_track = Node.query.filter(Node.endpoint.in_(nodes_to_track_input_list)).all()

    for node in nodes_to_track:
        node.track_block_height = True

    db.session.commit()

if __name__ == '__main__':
    activate()

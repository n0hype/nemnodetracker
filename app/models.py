from app import db


class Node(db.Model):
    __tablename__ = 'nodes'

    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    pub_key = db.Column(db.String(64), unique=True)
    name = db.Column(db.String(100), default='')
    endpoint = db.Column(db.String(100))
    active = db.Column(db.Boolean)
    importance = db.Column(db.Float(precision=32), default=0.0)
    track_block_height = db.Column(db.Boolean, default=False)
    block_height = db.relationship("BlockHeight", back_populates="node")

    def __repr__(self):
        return "<nodes(pub_key='%s', name='%s', endpoint='%s', active=%s, importance='%s', track_block_height='%s')>"\
            % (self.pub_key, self.name, self.endpoint, self.active, self.importance, self.track_block_height)


class NodeState(db.Model):

    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    time = db.Column(db.DateTime)
    no_importance_nodes_online = db.Column(db.Integer, default=0)
    high_importance_nodes_online = db.Column(db.Integer, default=0)
    booted_importance_sum = db.Column(db.Float(precision=32), default=0.0)

    def __repr__(self):
        return "<nodes(time='%s', no_importance_nodes_online='%s', high_importance_nodes_online='%s', booted_importance_sum=%s)>"\
            % (self.time, self.no_importance_nodes_online, self.high_importance_nodes_online, self.booted_importance_sum)


class BlockHeight(db.Model):

    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    node_id = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    chain_state_id = db.Column(db.Integer, db.ForeignKey('chain_state.id'))
    relative_height = db.Column(db.Integer, default=None)
    node = db.relationship("Node", back_populates="block_height")
    chain_state = db.relationship("ChainState", back_populates="block_height")

    def __repr__(self):
        return "<block_height(node_id='%s', chain_state_id='%s', relative_height='%s')>"\
            % (self.node_id, self.chain_state_id, self.relative_height)


class ChainState(db.Model):

    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    time = db.Column(db.DateTime)
    most_common_height = db.Column(db.Integer, default=0)
    most_common_count = db.Column(db.Integer, default=0)
    height_distribution = db.Column(db.String(2000))
    timeout_count = db.Column(db.Integer, default=0)
    nodes_tested = db.Column(db.Integer, default=0)
    block_height = db.relationship("BlockHeight", back_populates="chain_state")

    def __repr__(self):
        return ("<chain_state(time='%s', most_common_height='%s', most_common_count='%s', "
            "height_distribution='%s', timeout_count='%s', nodes_tested='%s')>")\
            % (self.time, self.most_common_height, self.most_common_count, self.height_distribution,\
            self.timeout_count, self.nodes_tested)


# if __name__ == '__main__':
#     #Base.metadata.create_all(engine)
#     #Base.metadata.drop_all(engine)

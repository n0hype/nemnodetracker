from flask import render_template
from app import app, cache
import app.views as v




@app.route('/')
@app.route('/index')
def index():
    node_heights_data = v.getNodesHeights()
    network_node_state_data = v.getNodeState()

    colors = app.config['GRAPH_COLORS']
    return render_template("index.html", title="Home", colors=colors, node_heights_data=node_heights_data, network_node_state_data=network_node_state_data)

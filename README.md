# NEM node tracker

Tracking nem nodes with some statistics.

This is alpha version.
current version is running on http://85.216.239.0/


### Installing
* set up db
 * flask db migrate
 * flask db upgrade

* initialize table of reachable nodes in NEM network
  * set DEFAULT_CLIENT and SEED_NODES in config.py
  * run python -m app.blockchain.updateNodeState
* activate your desired nodes for tracking:
  * set NODES_TO_TRACK in config.py (node endpoint has to already be in table of reachable nodes)
  * run python -m app.blockchain.activateNodesForTracking

* set up cron job for app.blockchain.updateNodeState and app.blockchain.updateBlockHeightState
  * depending on REQUEST_TIMEOUT and ASYNC_REQUEST_TIMEOUT in config.py, these scripts may take few seconds to run



* flask run or gunicorn nemnodetracker:app to run the web app


## Built With

* [Python](https://www.python.org/)
* [SQLAlchemy](https://www.sqlalchemy.org/)
* [Flask](https://flask.palletsprojects.com)
* [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/)
* [Chart.js](https://www.chartjs.org/docs/latest/)

## Authors

* n0hype '8980c10ead96daa7d38f34b4637d397c233eaa632e965556d2d3b771a7bf1579' [CHECK](https://www.xorbin.com/tools/sha256-hash-calculator)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

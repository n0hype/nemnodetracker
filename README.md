# NEM node tracker

Tracking nem nodes with some statistics.

This is alpha version.


### Installing

* resources/db_setup.py - set up database (use python -m resources.db_setup)
* updateNodeState.py - construct and update internal list of nem nodes
  * set DEFAULT_CLIENT
  * set cron job (recommended is once a day)
  * (this has to run at last once before next step)
* resources/activateNodesForTracking.py - run to activate some nodes for tracking, by default no specific node is tracked (use python -m resources.activateNodesForTracking)
* updateBlockHeightState.py - record block heights and other stuff
  * set cron job (recommended every 10 minutes)


* app.py to run the site


## Built With

* [Python](https://www.python.org/)
* [SQLAlchemy](https://www.sqlalchemy.org/)
* [Flask](https://flask.palletsprojects.com)
* [Chart.js](https://www.chartjs.org/docs/latest/)

## Authors

* n0hype '8980c10ead96daa7d38f34b4637d397c233eaa632e965556d2d3b771a7bf1579' [CHECK](https://www.xorbin.com/tools/sha256-hash-calculator)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

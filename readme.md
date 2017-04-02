Application used for measuring RAM and CPU usage on client machine and sending it to remote server.

## Stack description

* Client uses `ps aux` command to get load statistics. 
* Server runs autobahn websocket server
* Client sends stats in interval given by send-period flag
* Server stores stats in new table for every unique client. Sqlite3 is used.
* Additional script statistics.py allows for reading averaged data.


## Sample usage

* On server run: `python server.py --port <SERVER_PORT>`
* Check server ip with `ifconfig`
* On every client run `python client.py --addr <SERVER_IP> --port <SERVER_PORT> --send-period <SEND_PERIOD> --measure-period <MEASURE_PERIOD>`
Remember that send period must be grater than measure period.
* Server updates database when it is shut down or when client disconnected.
* Look at clients that where connected: `python statistics.py --show`
* Look at clients stats: `python statistics.py --show <PASS DESIRED CLIENTS IP> --average_time <AVERAGE_TIME_IN_SECONDS> 
--history-size <NUMBER OF OUTPUTED SAMPLES>`
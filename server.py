import argparse
import json
import logging
import sqlite3
from autobahn.asyncio.websocket import WebSocketServerProtocol
import asyncio
from autobahn.asyncio.websocket import WebSocketServerFactory
from netifaces import AF_INET
import netifaces as ni

from const import TIME_STAMP, CPU_USAGE, RAM_USAGE, database_path

CLIENT_PREFIX = 'client'


class ServerProtocol(WebSocketServerProtocol):

    SQL_CREATE_TABLE = "CREATE TABLE IF NOT EXISTS " + CLIENT_PREFIX + "_{ip} " + "({} REAL, {} REAL, {} REAL)"\
        .format(TIME_STAMP, CPU_USAGE, RAM_USAGE)
    SQL_INSERT_ROW = "INSERT INTO client_" + "{ip} " + "({}, {}, {}) ".format(TIME_STAMP, CPU_USAGE, RAM_USAGE) \
                     + "VALUES (:{}, :{}, :{})".format(TIME_STAMP, CPU_USAGE, RAM_USAGE)

    logger = None
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    def __init__(self):
        super().__init__()
        self.client_ip = None

    def onConnect(self, request):
        self.client_ip = request.peer.split(':')[1].replace('.', '_')
        self.logger.level = logging.DEBUG
        self.logger.debug('Client: {} connected'. format(request.peer))

    def onOpen(self):
        self.cursor.execute(self.SQL_CREATE_TABLE.format(ip=self.client_ip))

    def onMessage(self, payload, isBinary):
        msg = json.loads(payload.decode('ascii'))
        self.cursor.execute(self.SQL_INSERT_ROW.format(ip=self.client_ip), msg)
        self.logger.debug('{}: {}'.format(self.client_ip, msg))

    def onClose(self, wasClean, code, reason):
        self.connection.commit()
        self.logger.debug('Client: {} disconnected'.format(self.client_ip))


def parse_args():

    parser = argparse.ArgumentParser(
        description='Server accepting connection from remote clients via websocket protocol. The server saves'
                    'resource usage statistics in database',
        prog='Stats Server')

    parser.add_argument('--port', '-p', help='Application port.', type=int)

    return parser.parse_args()

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    server_logger = logging.getLogger('server')
    ServerProtocol.logger = server_logger

    args = parse_args()

    factory = WebSocketServerFactory()
    factory.protocol = ServerProtocol

    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    def_gw_device = ni.gateways()['default'][ni.AF_INET][1]
    ip = ni.ifaddresses(def_gw_device)[AF_INET][0]['addr']
    server_coroutine = loop.create_server(factory, ip, args.port)
    server_logger.info('Starting server with address: {}:{}'.format(ip, args.port))
    server = loop.run_until_complete(server_coroutine)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server_logger.info('Closing server')
        server.close()
        ServerProtocol.connection.commit()
        ServerProtocol.connection.close()
        loop.close()

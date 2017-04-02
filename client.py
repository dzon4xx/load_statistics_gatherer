import time
import json
import subprocess

from autobahn.asyncio.websocket import WebSocketClientProtocol

from const import CPU_USAGE, RAM_USAGE, TIME_STAMP

SEND_PERIOD = 1
MEASURE_PERIOD = 0.5


class Stats:
    CPU_POS = 2
    RAM_POS = 3

    def __init__(self, measure_period):
        self.measure_period = measure_period

    def get_stats(self):
        result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE).stdout.decode('ascii').split('\n')
        cpu_usage = 0
        mem_usage = 0
        for stats in result[1:-1]:
            stats = stats.split()
            cpu_usage += float(stats[self.CPU_POS].replace(',', '.'))
            mem_usage += float(stats[self.RAM_POS].replace(',', '.'))

        return {CPU_USAGE: cpu_usage, RAM_USAGE: mem_usage}

    async def resource_usage(self, client):
        while True:
            stats = self.get_stats()
            await client.stats_queue.put(stats)
            await asyncio.sleep(self.measure_period)


class ClientProtocol(WebSocketClientProtocol):

    stats_queue = None
    logger = None

    def onClose(self, wasClean, code, reason):
        self.logger.info('Closed connection')

    async def send_stats(self, send_period):
        last_timestamp = time.time()
        while True:
            await asyncio.sleep(send_period)
            stats = await self.average_stats()
            time_stamp = time.time()
            stats[TIME_STAMP] = (time_stamp + last_timestamp)/2  # Take time in the middle of measurements
            last_timestamp = time_stamp

            self.sendMessage(json.dumps(stats).encode('ascii'))

    async def average_stats(self):
        all_stats = {CPU_USAGE: 0, RAM_USAGE: 0}
        measurement = 0
        while not self.stats_queue.empty():
            stats = await self.stats_queue.get()
            for stat_name, stat in stats.items():
                all_stats[stat_name] += stat
            measurement += 1

        return {stat_name: stat / measurement for stat_name, stat in all_stats.items()}


def parse_args():

    parser = argparse.ArgumentParser(
        description='Client sending load statistics over websocket protocol to remote server',
        prog='Stats Client')

    parser.add_argument('--addr', '-a', help='Ip address of remote server.', required=True)
    parser.add_argument('--port', '-p', help='Port on server application.', type=int, required=True)
    parser.add_argument('--send-period', '-sp',
                        help='Frequency of sending load stats to remote server', default=SEND_PERIOD, type=int)
    parser.add_argument('--measure-period', '-mp',
                        help='Frequency of measuring load on current machine', default=MEASURE_PERIOD, type=int)

    args = parser.parse_args()

    if args.send_period < args.measure_period:
        raise ValueError('Send period: {} can\'t be smaller than measure period: {}'.format(args.send_period,
                                                                                            args.measure_period))
    return args

if __name__ == "__main__":
    import asyncio
    from autobahn.asyncio.websocket import WebSocketClientFactory
    import argparse
    import logging
    logging.basicConfig(level=logging.DEBUG)

    logger = logging.getLogger('client')
    ClientProtocol.logger = logger

    args = parse_args()

    factory = WebSocketClientFactory()
    factory.protocol = ClientProtocol
    loop = asyncio.get_event_loop()
    logger.info('Creating connection')
    coro = loop.create_connection(factory, args.addr, args.port)
    selector_socket, client = loop.run_until_complete(coro)

    client.stats_queue = asyncio.Queue()

    asyncio.ensure_future(client.send_stats(args.send_period))
    asyncio.ensure_future(Stats(args.measure_period).resource_usage(client))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Closing program')
        client.sendClose()
        loop.close()

#!/usr/bin/python

import argparse
import time
import calendar
import logging
import pika
import threading
import queue
import sys
import socket
from pika.exceptions import AMQPConnectionError

class ProducerBroker(object):

    exchange = 'posrep-raw'
    exchange_type = 'fanout'
    routing_key = None

    def __init__(self, amqp_url, data_queue):
        self.log = logging.getLogger("producer")
        self._connection = None
        self._channel = None
        self._closing = False
        self._url = amqp_url
        self._data_queue = data_queue

    def connect(self):
        self.log.info('Connecting to %s', self._url)
        return pika.SelectConnection(pika.URLParameters(self._url), self.on_connection_open, stop_ioloop_on_close=False)

    def on_connection_open(self, unused_connection):
        self.log.info('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        self.log.info('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if self._closing:
            self.log.info('Connection closed expectedly')
            self._connection.ioloop.stop()
        else:
            self.log.warning('Connection closed unexpected, reopening in 5 seconds: (%s) %s', reply_code, reply_text)
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        if not self._closing:

            # Create a new connection
            self._connection = self.connect()

            # There is now a new connection, needs a new ioloop to run
            self._connection.ioloop.start()

    def open_channel(self):
        self.log.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        self.log.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange()

    def add_on_channel_close_callback(self):
        self.log.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        self.log.warning('Channel %i was closed: (%s) %s', channel, reply_code, reply_text)
        self._connection.close()

    def setup_exchange(self):
        self.log.info('Declaring exchange %s', self.exchange)
        self._channel.exchange_declare(self.on_exchange_declareok, self.exchange, self.exchange_type, durable=True)

    def on_exchange_declareok(self, unused_frame):
        self.log.info('Exchange declared')
        self.work()

    def close_channel(self):
        self.log.info('Closing the channel')
        if self._channel:
            self._channel.close()

    def run(self):
        self._connection = self.connect()
        self._connection.ioloop.start()            

    def work(self):
        while not self._closing:
            try:
                self.log.debug("waiting for data ...")
                data = self._data_queue.get(timeout=1)
                hexdata = data.encode("hex")                
                self.log.debug("submitting message: %s", hexdata)
                unixtime = calendar.timegm(time.gmtime())
                properties = pika.BasicProperties(timestamp=unixtime)
                self._channel.basic_publish(exchange=self.exchange, routing_key='', properties=properties, body=data)
            except queue.Empty:
                continue
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception:
                self.log.error('submission failed', exc_info=True)
                if self._channel == None:
                    self.reconnect()
                    break

    def stop(self):
        self.log.info('Stopping')
        self._closing = True
        self.close_channel()
        self.close_connection()
        self._connection.ioloop.start()
        self.log.info('Stopped')

    def close_connection(self):
        self.log.info('Closing connection')
        self._closing = True
        self._connection.close()

class ComsumerBroker(object):

    def __init__(self, ip, port, data_queue):
        self.log = logging.getLogger("consumer")
        self._socket = None
        self._ip = ip
        self._port = port
        self._data_queue = data_queue

    def connect(self):
        self.log.info('Connecting to %s:%s', self._ip, self._port)
        sock = socket.socket(
            socket.AF_INET, # Internet
            socket.SOCK_DGRAM) # UDP
        sock.settimeout(5.0)
        sock.bind((self._ip, self._port))
        return sock

    def run(self):
        self._socket = self.connect()

        while True:
            try:
                data, addr = self._socket.recvfrom(4096) # buffer size is 4096 bytes
                hexdata = data.encode("hex")                
                self.log.debug("received message: %s", hexdata)                
                self._data_queue.put(data)
                self.log.debug("queue stats (size) (%d)", self._data_queue.qsize())
            except socket.timeout:
                self.log.debug("queue stats (size) (%d)", self._data_queue.qsize())
            except KeyboardInterrupt:
                break
            except Exception:
                self.log.error('receive failed', exc_info=True)

def main():

    parser = argparse.ArgumentParser(
        description='udp2amqp: UDP-package to AMQP relay server'
    )
    parser.add_argument("ampq_url", metavar='AMPQ_URL', help="amqp url for destination")
    parser.add_argument("udp_port", metavar='UDP_PORT', help="udp port for source", type=int)
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")

    args = parser.parse_args()

    log = logging.getLogger()
    format=('%(asctime)s %(levelname)s %(name)s %(message)s')
        
    if args.verbose:
        logging.basicConfig(filename='udp2amqp.log', level=logging.DEBUG, format=format)
        logging.getLogger().addHandler(logging.StreamHandler())
    else:
        logging.basicConfig(filename='udp2amqp.log', level=logging.INFO, format=format)


    log.info("udp2amqp is starting.")

    data_queue = queue.Queue(0)

    producerBroker = ProducerBroker(amqp_url=args.ampq_url, data_queue=data_queue)
    producerThread = threading.Thread(target=producerBroker.run)
    producerThread.daemon = True
    producerThread.start()

    hostname = socket.gethostname();
    ip = socket.gethostbyname(hostname)

    consumerBroker = ComsumerBroker(ip=ip, port=args.udp_port, data_queue=data_queue)

    try:
        consumerBroker.run()
    finally:
        log.info("udp2amqp is stopping.")


    log.info("udp2amqp has stopped.")

if __name__ == '__main__':
    main()
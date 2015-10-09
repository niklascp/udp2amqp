# udp2amqp
udp2amqp: a simple python script for relaying raw UDP-packages to a message queue using AMQP (Advanced Message Queuing Protocol), e.g. [Apache ActiveMQ](http://activemq.apache.org/) or [RabbitMQ](https://www.rabbitmq.com/).

## Prerequisites
- Python 3.3+
- [Pika for Python](https://github.com/pika/pika)

## Usage
Usage is pretty simple:
```
usage: udp2amqp.py [-h] [-v] AMPQ_URL UDP_PORT

udp2amqp: UDP-package to AMQP relay server

positional arguments:
  AMPQ_URL       amqp url for destination
  UDP_PORT       udp port for source
```

For example, the following will listen for udp packages at port 2011 and relay them to myampqserver.local on port 5672:
```
.\udp2amqp.py "amqp://username:password@myampqserver.local:5672" 2011 
```

## History
The script was originally developed as part of a realtime analysis program for public transportation in Greater Copenhagen, Denmark and has later been used for other [IoT](http://en.wikipedia.org/wiki/Internet_of_Things)-applications.

## License
Copyright (c) 2015 Niklas Christoffer Petersen

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

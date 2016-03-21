#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import logging.config
import unittest, threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

from desrunner import DesRunner

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

server = None


def setUpModule():
    global server
    server_address = ('', 8000)
    handler_class = SimpleHTTPRequestHandler
    server = HTTPServer(server_address, handler_class)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    logger.debug("Starting server at http://localhost:8000/")
    t.start()


def tearDownModule():
    global server
    logger.debug("Closing server at http://localhost:8000/")
    server.server_close()


class TestRunner(unittest.TestCase):

    def test01__init__(self):
        with self.assertRaises(FileNotFoundError):
            DesRunner()




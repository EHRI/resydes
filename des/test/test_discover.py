#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import logging.config
import threading
import unittest
import des.processor as proc
from des.processor_listener import SitemapWriter
from http.server import HTTPServer, SimpleHTTPRequestHandler
from des.discover import Discoverer
from des.status import Status
from des.config import Config
from des.location_mapper import DestinationMap


logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


def setUpModule():
    global server
    server_address = ('', 8000)
    handler_class = SimpleHTTPRequestHandler
    server = HTTPServer(server_address, handler_class)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    logger.debug("Starting server at http://localhost:8000/")
    t.start()
    proc.processor_listeners.append(SitemapWriter())
    Config._set_config_filename("test-files/config.txt")
    Config().__drop__()
    DestinationMap._set_map_filename("test-files/desmap.txt")
    DestinationMap().__drop__()
    DestinationMap().__set_destination__("http://localhost:8000/rs/source/discover/", "rs/destination/discover")


def tearDownModule():
    global server
    logger.debug("Closing server at http://localhost:8000/")
    server.server_close()


class TestDiscoverer(unittest.TestCase):

    def test01_well_known(self):
        uri = "http://localhost:8000/rs/source/discover/loc1"
        discoverer = Discoverer(uri)

        processor = discoverer.get_processor()
        self.assertIsInstance(processor, proc.Sodesproc)
        self.assertEqual(processor.status, Status.document)

    def test02_capabilitylist(self):
        uri = "http://localhost:8000/rs/source/discover/loc1/capabilitylist.xml"
        discoverer = Discoverer(uri)

        processor = discoverer.get_processor()
        self.assertIsInstance(processor, proc.Capaproc)
        self.assertEqual(processor.status, Status.document)

    def test03_try_link_html(self):
        uri = "http://localhost:8000/rs/source/discover/loc1/page.html"
        discoverer = Discoverer(uri)

        processor = discoverer.get_processor()
        self.assertIsInstance(processor, proc.Capaproc)

    def test04_try_link_corrupt_html(self):
        uri = "http://localhost:8000/rs/source/discover/loc1/corrupt_page.html"
        discoverer = Discoverer(uri)

        processor = discoverer.get_processor()
        self.assertIsNone(processor)

    def test05_try_link_absent_html(self):
        uri = "http://localhost:8000/rs/source/discover/loc1/no_page.html"
        discoverer = Discoverer(uri)

        processor = discoverer.get_processor()
        self.assertIsNone(processor)

    def test06_try_link_unparsable_html(self):
        uri = "http://localhost:8000/rs/source/discover/loc1/unparsable.html"
        discoverer = Discoverer(uri)

        processor = discoverer.get_processor()
        self.assertIsNone(processor)

    def test07_try_robots(self):
        uri = "http://localhost:8000/rs/source/discover/loc2"
        discoverer = Discoverer(uri)

        processor = discoverer.get_processor()
        self.assertIsInstance(processor, proc.Reliproc)
        processor.read_source()

    def test08_try_robots_with_netloc(self):
        DestinationMap().__remove_destination__("http://localhost:8000/rs/source/discover/")
        Config().__set_prop__(Config.key_use_netloc, "True")
        uri = "http://localhost:8000/rs/source/discover/loc2"
        discoverer = Discoverer(uri)

        processor = discoverer.get_processor()
        self.assertIsInstance(processor, proc.Reliproc)
        processor.read_source()

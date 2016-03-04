#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest, logging, logging.config, threading, resync.resource_container
from des.processor import Discoverer, Status, Relisync
from des.config import Config
from des.location_mapper import DestinationMap
from http.server import HTTPServer, SimpleHTTPRequestHandler

from unittest.mock import MagicMock

logging.config.fileConfig('logging.conf')

logger = logging.getLogger(__name__)


class TestDiscoverer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.__start_http_server__()

    @classmethod
    def tearDownClass(cls):
        cls.__close_http_server__()

    @classmethod
    def __start_http_server__(cls):
        server_address = ('', 8000)
        handler_class = SimpleHTTPRequestHandler
        cls.server = HTTPServer(server_address, handler_class)
        t = threading.Thread(target=cls.server.serve_forever)
        t.daemon = True
        logger.debug("Starting server at http://localhost:8000/")
        t.start()

    @classmethod
    def __close_http_server__(cls):
        logger.debug("Closing server at http://localhost:8000/")
        cls.server.server_close()

    def test01_process_source(self):
        # no connection to non-existent uri
        base_uri = "http://ditbestaatechtniet.com/out/there"
        discoverer = Discoverer(base_uri)
        self.assertTrue(discoverer.base_uri.endswith("/"))
        discoverer.read_source()
        self.assertFalse(discoverer.source_status)
        self.assertEqual(1, len(discoverer.exceptions))

        self.assertEqual(Status.read_error, discoverer.status)
        discoverer.process_source()
        self.assertEqual(Status.read_error, discoverer.status)

    def test02_process_source(self):
        # connection but no .well-known/...
        base_uri = "http://localhost:8000/rs/source/s2/"
        discoverer = Discoverer(base_uri)
        discoverer.read_source()
        self.assertEqual(404, discoverer.source_status)
        self.assertEqual(1, len(discoverer.exceptions))

        self.assertEqual(Status.read_error, discoverer.status)
        discoverer.process_source()
        self.assertEqual(Status.read_error, discoverer.status)

    def test03_process_source_(self):
        # connection and unreadable resourcesync
        base_uri = "http://localhost:8000/rs/source/s3/"
        discoverer = Discoverer(base_uri)
        discoverer.read_source()
        self.assertEqual(200, discoverer.source_status)
        self.assertEqual(1, len(discoverer.exceptions))

        self.assertEqual(Status.read_error, discoverer.status)
        discoverer.process_source()
        self.assertEqual(Status.read_error, discoverer.status)

    def test04_process_source(self):
        # connection and resourcesync is xml but not sitemap
        base_uri = "http://localhost:8000/rs/source/s4/"
        discoverer = Discoverer(base_uri)
        discoverer.read_source()
        self.assertEqual(200, discoverer.source_status)
        self.assertFalse(discoverer.source_description)
        self.assertEqual(1, len(discoverer.exceptions))

        self.assertEqual(Status.read_error, discoverer.status)
        discoverer.process_source()
        self.assertEqual(Status.read_error, discoverer.status)

    def test05_process_source(self):
        # connection and readable resourcesync but capability is not 'description'
        base_uri = "http://localhost:8000/rs/source/s5/"
        discoverer = Discoverer(base_uri)
        discoverer.read_source()
        self.assertEqual(200, discoverer.source_status)
        self.assertFalse(discoverer.source_description)
        self.assertEqual(1, len(discoverer.exceptions))

        self.assertEqual(Status.read_error, discoverer.status)
        discoverer.process_source()
        self.assertEqual(Status.read_error, discoverer.status)

    def test06_process_source(self):
        # connection and readable resourcesync
        base_uri = "http://localhost:8000/rs/source/s6/"
        discoverer = Discoverer(base_uri)
        discoverer.read_source()
        self.assertEqual(200, discoverer.source_status)
        self.assertEqual(Status.document, discoverer.status)
        # discoverer.source_description is a resync.resource_container.ResourceContainer
        self.assertEqual("http://example.com/info_about_source.xml", discoverer.describedby_url)
        self.assertEqual(0, len(discoverer.exceptions))

        self.assertEqual(Status.document, discoverer.status)
        discoverer.process_source()
        self.assertEqual(Status.processed_with_exceptions, discoverer.status)
        self.assertEqual(3, len(discoverer.exceptions))

    def test10_process_source(self):
        base_uri = "http://localhost:8000/rs/source/s7/"
        discoverer = Discoverer(base_uri)
        discoverer.process_source()
        self.assertEqual(200, discoverer.source_status)
        self.assertEqual(1, len(discoverer.exceptions))
        self.assertEqual(Status.processed_with_exceptions, discoverer.status)


class TestRelisync(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Config._set_config_filename("test-files/config.txt")
        DestinationMap._set_map_filename("test-files/desmap.txt")

    def test01_no_destination(self):
        Config().__set_prop__(Config.key_use_netloc, "False")
        DestinationMap().__remove_destination__("http://bla.com")

        resource = MagicMock(uri="http://bla.com")

        relisync = Relisync(resource)
        relisync.process_source()
        self.assertEqual(1, len(relisync.exceptions))
        self.assertEqual("No destination for http://bla.com", relisync.exceptions[0])

        DestinationMap().__set_destination__("http://bla.com", "destination_x")
        relisync = Relisync(resource)
        relisync.process_source()
        self.assertEqual(0, len(relisync.exceptions))

        Config().__set_prop__(Config.key_use_netloc, "True")
        DestinationMap().__remove_destination__("http://bla.com")
        relisync = Relisync(resource)
        relisync.process_source()
        self.assertEqual(0, len(relisync.exceptions))
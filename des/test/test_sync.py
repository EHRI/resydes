#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os.path, logging, threading
import unittest

import des.reporter
from des.config import Config
from des.location_mapper import DestinationMap
from des.status import Status
from des.sync import Relisync, Chanlisync
from des.test.test_processor import __clear_destination__, __clear_sources_xml__, __create_resourcelist__, \
    __create_changelist__, __change_resource__, __add_resource__, __delete_resource__
from http.server import HTTPServer, SimpleHTTPRequestHandler


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


def tearDownModule():
    global server
    logger.debug("Closing server at http://localhost:8000/")
    server.server_close()


class TestRelisync(unittest.TestCase):

    def setUp(self):
        Config.__set_config_filename__("test-files/config.txt")
        Config().__drop__()
        DestinationMap.__set_map_filename__("test-files/desmap.txt")
        DestinationMap().__drop__()
        des.desclient.reset_instance()

    def test01_no_destination_no_connection(self):
        Config().__set_prop__(Config.key_use_netloc, "False")
        DestinationMap().__remove_destination__("http://bla.com")
        des.reporter.reset_instance()

        logger.debug("\n============ no destination =============\n")
        # returns at no destination
        relisync = Relisync("http://bla.com")
        self.assertEqual(Status.init, relisync.status)
        relisync.process_source()
        self.assertEqual(1, len(relisync.exceptions))
        self.assertEqual("No destination for http://bla.com", relisync.exceptions[0])
        self.assertEqual(Status.processed_with_exceptions, relisync.status)

        # cannot get connection and ends up in caught exception
        DestinationMap().__set_destination__("http://bla.com", "destination_x")
        logger.debug("\n============destination, no connection =============\n")
        relisync = Relisync("http://bla.com")
        relisync.process_source()
        self.assertEqual(1, len(relisync.exceptions))
        self.assertEqual(Status.processed_with_exceptions, relisync.status)
        reporter = des.reporter.instance()
        self.assertEqual(2, len(reporter.sync_status))
        self.assertIsNotNone(reporter.sync_status[0].exception)

        # using net location 'bla.com' as destination, still no connection
        Config().__set_prop__(Config.key_use_netloc, "True")
        DestinationMap().__remove_destination__("http://bla.com")
        logger.debug("\n=========== using netloc, still no connection ==============\n")
        relisync = Relisync("http://bla.com")
        relisync.process_source()
        self.assertEqual(1, len(relisync.exceptions))
        self.assertEqual(Status.processed_with_exceptions, relisync.status)
        self.assertEqual(3, len(reporter.sync_status))
        self.assertIsNotNone(reporter.sync_status[1].exception)

    def test02_process_audit(self):
        Config().__set_prop__(Config.key_use_netloc, "False")
        Config().__set_prop__(Config.key_audit_only, "True")
        DestinationMap().__set_destination__("http://localhost:8000/rs/source/s1", "rs/destination/d1")

        __clear_destination__("d1")
        __clear_sources_xml__("s1")
        __create_resourcelist__("s1")
        des.reporter.reset_instance()

        logger.debug("\n=========================\n")
        relisync = Relisync("http://localhost:8000/rs/source/s1/resourcelist.xml")
        relisync.process_source()

        self.assertEqual(0, len(relisync.exceptions))
        self.assertEqual(Status.processed, relisync.status)
        reporter = des.reporter.instance()
        self.assertEqual(1, len(reporter.sync_status))

        reporter.sync_status_to_file("logs/audit.csv")

    def test03_process_baseline(self):
        Config().__set_prop__(Config.key_use_netloc, "False")
        Config().__set_prop__(Config.key_audit_only, "False")
        DestinationMap().__set_destination__("http://localhost:8000/rs/source/s1", "rs/destination/d1")

        __clear_destination__("d1")
        __clear_sources_xml__("s1")
        __create_resourcelist__("s1")
        des.reporter.reset_instance()

        logger.debug("\n=========== create ==============\n")
        relisync = Relisync("http://localhost:8000/rs/source/s1/resourcelist.xml")
        relisync.process_source()

        self.assertEqual(0, len(relisync.exceptions))
        self.assertEqual(Status.processed, relisync.status)
        reporter = des.reporter.instance()
        # sync_status count: 1 for audit, 1 for create. expected 2
        # print(reporter.sync_status_to_string())
        self.assertEqual(2, len(reporter.sync_status))
        self.assertEqual(0, reporter.sync_status[0].same)
        self.assertEqual(3, reporter.sync_status[0].created)
        self.assertEqual(0, reporter.sync_status[0].updated)
        self.assertEqual(0, reporter.sync_status[0].deleted)
        self.assertEqual(0, reporter.sync_status[0].to_delete)
        self.assertIsNone(reporter.sync_status[0].exception)
        #reporter.sync_status_to_file("logs/baseline.csv")

        logger.debug("\n============ update =============\n")
        relisync = Relisync("http://localhost:8000/rs/source/s1/resourcelist.xml")
        relisync.process_source()

        self.assertEqual(0, len(relisync.exceptions))
        self.assertEqual(Status.processed, relisync.status)
        reporter = des.reporter.instance()
        # sync_status count: 1 for audit, 1 for create (both from previous run), 1 for audit, no update. expected 3
        self.assertEqual(3, len(reporter.sync_status))
        self.assertEqual(3, reporter.sync_status[2].same)
        self.assertEqual(0, reporter.sync_status[2].created)
        self.assertEqual(0, reporter.sync_status[2].updated)
        self.assertEqual(0, reporter.sync_status[2].deleted)
        self.assertEqual(0, reporter.sync_status[2].to_delete)
        self.assertIsNone(reporter.sync_status[2].exception)

    def test04_process_baseline_netloc(self):
        Config().__set_prop__(Config.key_use_netloc, "True")
        Config().__set_prop__(Config.key_audit_only, "False")
        DestinationMap().__remove_destination__("http://localhost:8000/rs/source/s1")

        __clear_sources_xml__("s1")
        __create_resourcelist__("s1")
        if os.path.isdir("localhost:8000"):
            logger.debug("Expecting only audit")
            expected_sync_status_count = 1
        else:
            logger.debug("Expecting update")
            expected_sync_status_count = 2

        logger.debug("\n=========================\n")
        relisync = Relisync("http://localhost:8000/rs/source/s1/resourcelist.xml")
        relisync.process_source()

        self.assertEqual(0, len(relisync.exceptions))
        self.assertEqual(Status.processed, relisync.status)
        reporter = des.reporter.instance()
        # depends on whether test is run individually or in group
        #self.assertEqual(expected_sync_status_count, len(reporter.sync_status))

        reporter.sync_status_to_file("logs/baseline-netloc.csv")


class TestChanlisync(unittest.TestCase):

    def setUp(self):
        Config.__set_config_filename__("test-files/config.txt")
        Config().__drop__()
        DestinationMap.__set_map_filename__("test-files/desmap.txt")
        DestinationMap().__drop__()
        des.reporter.reset_instance()

    def test_01_no_change(self):
        Config().__set_prop__(Config.key_use_netloc, "False")
        Config().__set_prop__(Config.key_audit_only, "False")
        DestinationMap().__set_destination__("http://localhost:8000/rs/source/s1", "rs/destination/d1")

        __clear_destination__("d1")
        __clear_sources_xml__("s1")
        __create_resourcelist__("s1")

        logger.debug("\n=========== create ==============\n")
        relisync = Relisync("http://localhost:8000/rs/source/s1/resourcelist.xml")
        relisync.process_source()
        self.assertEqual(0, len(relisync.exceptions))
        self.assertEqual(Status.processed, relisync.status)

        __create_changelist__("s1")

        logger.debug("\n=========== no change ==============\n")
        chanlisync = Chanlisync("http://localhost:8000/rs/source/s1/changelist.xml")
        chanlisync.process_source()

        self.assertEqual(0, len(chanlisync.exceptions))
        self.assertEqual(Status.processed, chanlisync.status)
        reporter = des.reporter.instance()
        self.assertEqual(3, len(reporter.sync_status))
        #self.assertEqual(2, reporter.sync_status[2].same)
        self.assertIsNone(reporter.sync_status[2].same)
        self.assertEqual(0, reporter.sync_status[2].created)
        self.assertEqual(0, reporter.sync_status[2].updated)
        self.assertEqual(0, reporter.sync_status[2].deleted)
        self.assertEqual(0, reporter.sync_status[2].to_delete)
        self.assertIsNone(reporter.sync_status[2].exception)

        reporter.sync_status_to_file("logs/incremental.csv")

    def test_02_change(self):
        Config().__set_prop__(Config.key_use_netloc, "False")
        Config().__set_prop__(Config.key_audit_only, "False")
        DestinationMap().__set_destination__("http://localhost:8000/rs/source/s1", "rs/destination/d1")

        __clear_destination__("d1")
        __clear_sources_xml__("s1")
        __create_resourcelist__("s1")

        logger.debug("\n=========== create ==============\n")
        relisync = Relisync("http://localhost:8000/rs/source/s1/resourcelist.xml")
        relisync.process_source()
        self.assertEqual(0, len(relisync.exceptions))
        self.assertEqual(Status.processed, relisync.status)

        __change_resource__("s1", "resource1.txt")
        __create_changelist__("s1")

        logger.debug("\n=========== change ==============\n")
        chanlisync = Chanlisync("http://localhost:8000/rs/source/s1/changelist.xml")
        chanlisync.process_source()

        self.assertEqual(0, len(chanlisync.exceptions))
        self.assertEqual(Status.processed, chanlisync.status)
        reporter = des.reporter.instance()
        self.assertEqual(4, len(reporter.sync_status))
        #self.assertEqual(1, reporter.sync_status[3].same)
        self.assertIsNone(reporter.sync_status[3].same)
        self.assertEqual(0, reporter.sync_status[3].created)
        self.assertEqual(1, reporter.sync_status[3].updated)
        self.assertEqual(0, reporter.sync_status[3].deleted)
        self.assertEqual(0, reporter.sync_status[3].to_delete)
        self.assertIsNone(reporter.sync_status[3].exception)

        reporter.sync_status_to_file("logs/incremental-change.csv")

    def test_03_change_delete(self):
        Config().__set_prop__(Config.key_use_netloc, "False")
        Config().__set_prop__(Config.key_audit_only, "False")
        DestinationMap().__set_destination__("http://localhost:8000/rs/source/s2", "rs/destination/d2")

        __clear_destination__("d2")
        __clear_sources_xml__("s2")
        __add_resource__("s2", "added.txt")
        __create_resourcelist__("s2")

        logger.debug("\n=========== create ==============\n")
        relisync = Relisync("http://localhost:8000/rs/source/s2/resourcelist.xml")
        relisync.process_source()
        self.assertEqual(0, len(relisync.exceptions))
        self.assertEqual(Status.processed, relisync.status)

        __change_resource__("s2", "resource2.txt")
        __delete_resource__("s2", "added.txt")
        __create_changelist__("s2")

        des.reporter.reset_instance()
        #time.sleep(5)
        logger.debug("\n=========== update + delete ==============\n")
        chanlisync = Chanlisync("http://localhost:8000/rs/source/s2/changelist.xml")
        chanlisync.process_source()

        self.assertEqual(0, len(chanlisync.exceptions))
        self.assertEqual(Status.processed, chanlisync.status)

        reporter = des.reporter.instance()
        reporter.sync_status_to_file("logs/incremental-change-delete.csv")
        self.assertEqual(2, len(reporter.sync_status))
        self.assertIsNone(reporter.sync_status[1].same)
        self.assertEqual(0, reporter.sync_status[1].created)
        self.assertEqual(1, reporter.sync_status[1].updated)
        self.assertEqual(1, reporter.sync_status[1].deleted)
        self.assertEqual(1, reporter.sync_status[1].to_delete)
        self.assertIsNone(reporter.sync_status[1].exception)

        des.reporter.reset_instance()
        logger.debug("\n=========== no change ==============\n")
        chanlisync = Chanlisync("http://localhost:8000/rs/source/s2/changelist.xml")
        chanlisync.process_source()

        self.assertEqual(0, len(chanlisync.exceptions))
        self.assertEqual(Status.processed, chanlisync.status)

        reporter = des.reporter.instance()
        self.assertEqual(1, len(reporter.sync_status))
        self.assertIsNone(reporter.sync_status[0].same)
        self.assertEqual(0, reporter.sync_status[0].created)
        self.assertEqual(0, reporter.sync_status[0].updated)
        self.assertEqual(0, reporter.sync_status[0].deleted)
        self.assertEqual(0, reporter.sync_status[0].to_delete)
        self.assertIsNone(reporter.sync_status[0].exception)
#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest, logging, logging.config, threading, os.path, glob, shutil, pathlib, datetime
import des.reporter
from des.processor import Discoverer, Status, Relisync, Chanlisync
from des.config import Config
from des.location_mapper import DestinationMap
from http.server import HTTPServer, SimpleHTTPRequestHandler
from resync.client import Client

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


def __clear_sources_xml__(src):
        """
        remove all xml files from a rs/source subfolder
        :param src: 's1', 's2' etc.
        :return: None
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        s = os.path.join(abs_path, "rs/source", src, "*.xml")
        files = glob.glob(s)
        for f in files:
            os.remove(f)


def __clear_destination__(des):
        """
        remove all files from rs/destination subfolder.
        :param des: 'd1', 'd2' etc.
        :return: None
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        files = os.path.join(abs_path, "rs/destination", des, "files")
        shutil.rmtree(files, ignore_errors=True)


def __create_resourcelist__(src, checksum=True):
        """
        Create a resourcelist xml for the source denominated by src.
        :param src: 's1', 's2' etc.
        :param checksum: should checksums be added to the xml.
        :return: None
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        data = []
        path = os.path.join(abs_path, "rs/source", src, "files")
        for root, directories, filenames in os.walk(path):
            for filename in filenames:
                data.append(os.path.join(root,filename))

        paths = ",".join(data)

        outfile = os.path.join(abs_path, "rs/source", src, "resourcelist.xml")

        # create a resourcelist from the files in test/rs/source/{src}/files
        client = Client(checksum=checksum)
        prefix = "http://localhost:8000/rs/source/" + src + "/files"
        resourcedir = os.path.join(abs_path, "rs/source", src, "files")
        args = [prefix, resourcedir]

        client.set_mappings(args)
        client.write_resource_list(paths, outfile)


def __create_changelist__(src, checksum=True):
        """
        Create a changelist xml for the source denominated by src.
        :param src: 's1', 's2' etc.
        :param checksum: should checksums be added to the xml.
        :return: None
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        data = []
        path = os.path.join(abs_path, "rs/source", src, "files")
        for root, directories, filenames in os.walk(path):
            for filename in filenames:
                data.append(os.path.join(root,filename))

        paths = ",".join(data)

        outfile = os.path.join(abs_path, "rs/source", src, "changelist.xml")
        ref_sitemap = pathlib.Path(os.path.join(abs_path, "rs/source", src, "resourcelist.xml")).as_uri()

        # create a changelist from the files in test/rs/source/{src}/files based on ^that
        client = Client(checksum=checksum)
        prefix = "http://localhost:8000/rs/source/" + src + "/files"
        resourcedir = os.path.join(abs_path, "rs/source", src, "files")
        args = [prefix, resourcedir]

        client.set_mappings(args)
        client.write_change_list(paths=paths, outfile=outfile, ref_sitemap=ref_sitemap)


def __change_resource__(src, resource):
        """
        Change a resource
        :param src: 's1', 's2' etc.
        :param resource: filename, i.e. 'resource1.txt', 'resource2.txt' etc.
        :return:
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        filename = os.path.join(abs_path, "rs/source", src, "files", resource)
        with open(filename, "a") as file:
            file.write("\n%s" % str(datetime.datetime.now()))


def __add_resource__(src, resource):
        abs_path = os.path.dirname(os.path.abspath(__name__))
        filename = os.path.join(abs_path, "rs/source", src, "files", resource)
        with open(filename, "w") as file:
            file.write("\n%s" % str(datetime.datetime.now()))


def __delete_resource__(src, resource):
        """
        Delete a resource
        :param src: 's1', 's2' etc.
        :param resource: filename, i.e. 'resource1.txt', 'resource2.txt' etc.
        :return:
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        filename = os.path.join(abs_path, "rs/source", src, "files", resource)
        os.remove(filename)


class TestDiscoverer(unittest.TestCase):

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


class TestRelisync(unittest.TestCase):

    def setUp(self):
        Config._set_config_filename("test-files/config.txt")
        Config().__drop__()
        DestinationMap._set_map_filename("test-files/desmap.txt")
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
        self.assertEqual(2, len(reporter.sync_status))
        self.assertEqual(0, reporter.sync_status[0].same)
        self.assertEqual(2, reporter.sync_status[0].created)
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
        self.assertEqual(2, reporter.sync_status[2].same)
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
        Config._set_config_filename("test-files/config.txt")
        Config().__drop__()
        DestinationMap._set_map_filename("test-files/desmap.txt")
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
        DestinationMap().__set_destination__("http://localhost:8000/rs/source/s1", "rs/destination/d1")

        __clear_destination__("d1")
        __clear_sources_xml__("s1")
        __add_resource__("s1", "added.txt")
        __create_resourcelist__("s1")

        logger.debug("\n=========== create ==============\n")
        relisync = Relisync("http://localhost:8000/rs/source/s1/resourcelist.xml")
        relisync.process_source()
        self.assertEqual(0, len(relisync.exceptions))
        self.assertEqual(Status.processed, relisync.status)

        __change_resource__("s1", "resource2.txt")
        __delete_resource__("s1", "added.txt")
        __create_changelist__("s1")

        logger.debug("\n=========== change + delete ==============\n")
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
        self.assertEqual(1, reporter.sync_status[3].deleted)
        self.assertEqual(1, reporter.sync_status[3].to_delete)
        self.assertIsNone(reporter.sync_status[3].exception)

        reporter.sync_status_to_file("logs/incremental-change-delete.csv")

#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest, logging, logging.config, threading, des.desclient, des.reporter, os.path, pathlib, datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from des.config import Config
from resync.client import Client
from des.test.test_processor import __clear_destination__


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


def __create_resourcelist__(src, checksum=True, name="resourcelist.xml"):
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

        outfile = os.path.join(abs_path, "rs/source", src, name)

        # create a resourcelist from the files in test/rs/source/{src}/files
        client = Client(checksum=checksum)
        prefix = "http://localhost:8000/rs/source/" + src + "/files"
        resourcedir = os.path.join(abs_path, "rs/source", src, "files")
        args = [prefix, resourcedir]

        client.set_mappings(args)
        client.write_resource_list(paths, outfile)


def __create_changelist__(src, checksum=True, name="changelist.xml", rs_name="resourcelist.xml"):
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

        outfile = os.path.join(abs_path, "rs/source", src, name)
        ref_sitemap = pathlib.Path(os.path.join(abs_path, "rs/source", src, rs_name)).as_uri()

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



class TestDesClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Config.__set_config_filename__("test-files/config.txt")

    def test01_instance(self):
        desclient1 = des.desclient.instance()
        self.assertIsNotNone(desclient1)

        desclient2 = des.desclient.instance()
        self.assertEqual(desclient1, desclient2)

        des.desclient.reset_instance()
        desclient3 = des.desclient.instance()
        self.assertIsNotNone(desclient3)
        self.assertNotEqual(desclient1, desclient3)

    def test02_baseline_or_audit(self):
        __clear_destination__("d1")
        __create_resourcelist__("s1", name="weird_name.xlm")
        uri = "http://localhost:8000/rs/source/s1/weird_name.xlm"
        destination = "rs/destination/d1"
        allow_deletion = True
        audit_only = False
        des.reporter.reset_instance()

        logger.debug("\n============ baseline or audit =============\n")
        desclient = des.desclient.instance()
        desclient.set_mappings((uri, destination))
        desclient.baseline_or_audit(allow_deletion, audit_only)

        self.assertEqual(2, len(des.reporter.instance().sync_status))

    def test03_incremental(self):
        resourcelist_name = "weird_name.xlm"
        changelist_name = "even_stranger.foo"
        __create_resourcelist__("s1", name=resourcelist_name)
        __change_resource__("s1", "resource1.txt")
        __create_changelist__("s1", name=changelist_name, rs_name=resourcelist_name)

        uri = "http://localhost:8000/rs/source/s1/" + changelist_name
        destination = "rs/destination/d1"
        allow_deletion = True
        des.reporter.reset_instance()

        logger.debug("\n============ first incremental =============\n")
        desclient = des.desclient.instance()
        desclient.set_mappings((uri, destination))
        from_datetime = "1999"
        desclient.incremental(allow_deletion=allow_deletion, from_datetime=from_datetime)

        self.assertEqual(2, len(des.reporter.instance().sync_status))

        des.reporter.reset_instance()
        logger.debug("\n============ second incremental =============\n")
        desclient.incremental(allow_deletion=allow_deletion)

        self.assertEqual(1, len(des.reporter.instance().sync_status))



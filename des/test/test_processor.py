#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import datetime, glob, logging, logging.config, os.path, pathlib, shutil, threading, unittest, des.processor
from http.server import HTTPServer, SimpleHTTPRequestHandler

from des.processor import Sodesproc, Redumpproc
from des.status import Status
from des.config import Config
from des.location_mapper import DestinationMap
from des.processor_listener import SitemapWriter
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
    files = os.path.join(abs_path, "rs/destination", des, "resources")
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


class TestSodesproc(unittest.TestCase):

    def test01_process_source(self):
        # no connection to non-existent uri
        base_uri = "http://ditbestaatechtniet.com/out/there"
        sdproc = Sodesproc(base_uri)
        self.assertTrue(sdproc.base_uri.endswith("/"))
        sdproc.read_source()
        self.assertFalse(sdproc.source_status)
        self.assertEqual(1, len(sdproc.exceptions))

        self.assertEqual(Status.read_error, sdproc.status)
        sdproc.process_source()
        self.assertEqual(Status.read_error, sdproc.status)

    def test02_process_source(self):
        # connection but no .well-known/...
        base_uri = "http://localhost:8000/rs/source/s2/"
        sdproc = Sodesproc(base_uri)
        sdproc.read_source()
        self.assertEqual(404, sdproc.source_status)
        self.assertEqual(1, len(sdproc.exceptions))

        self.assertEqual(Status.read_error, sdproc.status)
        sdproc.process_source()
        self.assertEqual(Status.read_error, sdproc.status)

    def test03_process_source_(self):
        # connection and unreadable resourcesync
        base_uri = "http://localhost:8000/rs/source/s3/"

        sdproc = Sodesproc(base_uri)
        sdproc.read_source()
        self.assertEqual(200, sdproc.source_status)
        self.assertEqual(1, len(sdproc.exceptions))

        self.assertEqual(Status.read_error, sdproc.status)
        sdproc.process_source()
        self.assertEqual(Status.read_error, sdproc.status)

    def test04_process_source(self):
        # connection and resourcesync is xml but not sitemap
        base_uri = "http://localhost:8000/rs/source/s4/"
        sdproc = Sodesproc(base_uri)
        sdproc.read_source()
        self.assertEqual(200, sdproc.source_status)
        self.assertEqual(1, len(sdproc.exceptions))

        self.assertEqual(Status.read_error, sdproc.status)
        sdproc.process_source()
        self.assertEqual(Status.read_error, sdproc.status)

    def test05_process_source(self):
        # connection and readable resourcesync but capability is not 'description'
        base_uri = "http://localhost:8000/rs/source/s5/"
        sdproc = Sodesproc(base_uri)
        sdproc.read_source()
        self.assertEqual(200, sdproc.source_status)
        self.assertEqual(1, len(sdproc.exceptions))

        self.assertEqual(Status.read_error, sdproc.status)
        sdproc.process_source()
        self.assertEqual(Status.read_error, sdproc.status)

    def test06_process_source(self):
        # connection and readable resourcesync
        base_uri = "http://localhost:8000/rs/source/s6/"
        sdproc = Sodesproc(base_uri)
        sdproc.read_source()
        self.assertEqual(200, sdproc.source_status)
        self.assertEqual(Status.document, sdproc.status)
        # sdproc.source_description is a resync.resource_container.ResourceContainer
        self.assertEqual("http://example.com/info_about_source.xml", sdproc.describedby_url)
        self.assertEqual(0, len(sdproc.exceptions))

        self.assertEqual(Status.document, sdproc.status)
        sdproc.process_source()
        self.assertEqual(Status.processed_with_exceptions, sdproc.status)
        self.assertEqual(3, len(sdproc.exceptions))

    def test07_process_source(self):
        # connection and readable resourcesync, write sitemap to file
        try:
            shutil.rmtree("rs/destination/d6/sitemaps")
        except:
            pass
        Config.__set_config_filename__("test-files/config.txt")
        Config().__drop__()
        DestinationMap.__set_map_filename__("test-files/desmap.txt")
        DestinationMap().__drop__()
        des.reporter.reset_instance()
        Config().__set_prop__(Config.key_use_netloc, "False")
        Config().__set_prop__(Config.key_audit_only, "False")
        DestinationMap().__set_destination__("http://localhost:8000/rs/source/s6", "rs/destination/d6")
        des.processor.processor_listeners.append(SitemapWriter())
        base_uri = "http://localhost:8000/rs/source/s6/"

        sdproc = Sodesproc(base_uri)
        sdproc.read_source()
        self.assertEqual(200, sdproc.source_status)
        self.assertEqual(Status.document, sdproc.status)
        self.assertTrue(os.path.isfile("rs/destination/d6/sitemaps/.well-known/resourcesync"))



class TestRedumpproc(unittest.TestCase):

    def testRead(self):
        uri = "http://localhost:8000/rs/source/redump/resourcedump.xml"
        redumpproc = Redumpproc(uri)

        redumpproc.process_source()



#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, logging.config, threading, unittest, os, des.dump
from http.server import HTTPServer, SimpleHTTPRequestHandler
from resync.dump import Dump
from resync.client import Client
from des.dump import Redump
from des.config import Config
from des.processor_listener import SitemapWriter
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


def tearDownModule():
    global server
    logger.debug("Closing server at http://localhost:8000/")
    server.server_close()


def __create_resourcelist__(src, checksum=True):
    """
    Create a resourcelist for the source denominated by src.
    :param src: 's1', 's2', 'foo' etc.
    :param checksum: should checksums be added to the xml.
    :return: resync.resource_list.ResourceList
    """
    abs_path = os.path.dirname(os.path.abspath(__name__))
    data = []
    path = os.path.join(abs_path, "rs/source", src, "files")
    for root, directories, filenames in os.walk(path):
        for filename in filenames:
            data.append(os.path.join(root,filename))

    paths = ",".join(data)

    # create a resourcelist from the files in test/rs/source/{src}/files
    client = Client(checksum=checksum)
    prefix = "http://localhost:8000/rs/source/" + src + "/files"
    resourcedir = os.path.join(abs_path, "rs/source", src, "files")
    args = [prefix, resourcedir]

    client.set_mappings(args)
    rl = client.build_resource_list(paths=paths, set_path=True)
    return rl


def __write_dump__():
    rl = __create_resourcelist__("redump")
    d = Dump(resources=rl)
    d.write(basename="rs/source/redump/rd_")

@unittest.skip("Dump implementations from resync hardly sufficient. Need complete new implementation")
class TestRedump(unittest.TestCase):

    def setUp(self):
        Config.__set_config_filename__("test-files/config.txt")
        Config().__drop__()
        des.dump.dump_listeners.append(SitemapWriter())
        DestinationMap().__set_destination__("http://localhost:8000/rs/source", "rs/destination/d7")

    def test01_process_dump(self):
        __write_dump__()
        pack_uri = "http://localhost:8000/rs/source/redump/rd_00000.zip"

        logger.debug("\n============ process dump =============\n")
        dump = Redump(pack_uri)
        dump.process_dump()


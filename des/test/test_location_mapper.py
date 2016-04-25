#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest, logging, logging.config

from des.location_mapper import DestinationMap

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


class TestDestinationMap(unittest.TestCase):

    def setUp(self):
        DestinationMap._set_map_filename("test-files/desmap.txt")
        DestinationMap().__drop__()

    def test01_shorten(self):
        uri = "http://long.name.com/des/ti/na/tion/path/file.xml"
        new_uri, new_path = DestinationMap.shorten(uri)
        self.assertEqual("http://long.name.com/des/ti/na/tion/path", new_uri)
        self.assertEqual("/des/ti/na/tion/path", new_path)

        new_uri, new_path = DestinationMap.shorten(new_uri)
        self.assertEqual("http://long.name.com/des/ti/na/tion", new_uri)
        self.assertEqual("/des/ti/na/tion", new_path)

        new_uri, new_path = DestinationMap.shorten(new_uri)
        self.assertEqual("http://long.name.com/des/ti/na", new_uri)
        self.assertEqual("/des/ti/na", new_path)

        new_uri, new_path = DestinationMap.shorten(new_uri)
        self.assertEqual("http://long.name.com/des/ti", new_uri)
        self.assertEqual("/des/ti", new_path)

        new_uri, new_path = DestinationMap.shorten(new_uri)
        self.assertEqual("http://long.name.com/des", new_uri)
        self.assertEqual("/des", new_path)

        new_uri, new_path = DestinationMap.shorten(new_uri)
        self.assertEqual("http://long.name.com", new_uri)
        self.assertEqual("", new_path)

        new_uri, new_path = DestinationMap.shorten(new_uri)
        self.assertEqual("http://long.name.com", new_uri)
        self.assertEqual("", new_path)

    def test02_shorten(self):
        uri = "file:///Users/you/git"

        new_uri, new_path = DestinationMap.shorten(uri)
        self.assertEqual("file:///Users/you", new_uri)
        self.assertEqual("/Users/you", new_path)

        new_uri, new_path = DestinationMap.shorten(new_uri)
        self.assertEqual("file:///Users", new_uri)
        self.assertEqual("/Users", new_path)

        new_uri, new_path = DestinationMap.shorten(new_uri)
        self.assertEqual("file://", new_uri)
        self.assertEqual("", new_path)

        new_uri, new_path = DestinationMap.shorten(new_uri)
        self.assertEqual("file://", new_uri)
        self.assertEqual("", new_path)

    def test03_shorten(self):
        uri = "https://docs.python.org/3.4/library/urllib.parse.html?highlight=urlparse#urllib.parse.urlparse"
        new_uri, new_path = DestinationMap.shorten(uri)
        self.assertEqual("https://docs.python.org/3.4/library", new_uri)
        self.assertEqual("/3.4/library", new_path)

    def test04_set_filename_once(self):
        DestinationMap._set_map_filename("test-files/desmap.txt")
        self.assertEqual("test-files/desmap.txt", DestinationMap._get_map_filename())
        desmap = DestinationMap()
        self.assertEqual("test-files/desmap.txt", desmap._map_filename)

        DestinationMap._set_map_filename("test-files/other-desmap.txt")
        self.assertEqual("test-files/desmap.txt", DestinationMap._get_map_filename())
        desmap = DestinationMap()
        self.assertEqual("test-files/desmap.txt", desmap._map_filename)

    def test05_find_destination(self):
        DestinationMap._set_map_filename("test-files/desmap.txt")
        desmap = DestinationMap()

        uri = "http://long.name.com/path/to/resource.xml"
        base_uri, destination = desmap.find_destination(uri)
        self.assertEqual("http://long.name.com", base_uri)
        self.assertEqual("./destination1", destination)

        uri = "http://long.name.com/path/to/"
        base_uri, destination = desmap.find_destination(uri)
        self.assertEqual("http://long.name.com", base_uri)
        self.assertEqual("./destination1", destination)

        uri = "http://long.name.com/"
        base_uri, destination = desmap.find_destination(uri)
        self.assertEqual("http://long.name.com", base_uri)
        self.assertEqual("./destination1", destination)

        uri = "http://long.name.com"
        base_uri, destination = desmap.find_destination(uri)
        self.assertEqual("http://long.name.com", base_uri)
        self.assertEqual("./destination1", destination)

        # explicit path to resource in desmap
        uri = "https://first.com:8080/path1"
        base_uri, destination = desmap.find_destination(uri)
        self.assertEqual("https://first.com:8080", base_uri)
        self.assertIsNone(destination)

        uri = "https://first.com:8080/path1/to/resource.xml"
        base_uri, destination = desmap.find_destination(uri)
        self.assertEqual("https://first.com:8080/path1/to/resource.xml", base_uri)
        self.assertEqual("./destination2", destination)

        uri = "https://first.com:8080/path2/"
        base_uri, destination = desmap.find_destination(uri)
        self.assertEqual("https://first.com:8080/path2", base_uri)
        self.assertEqual("./destination3", destination)

        uri = "https://first.com:8080/path2"
        base_uri, destination = desmap.find_destination(uri)
        self.assertEqual("https://first.com:8080/path2", base_uri)
        self.assertEqual("./destination3", destination)

        #
        uri = "https://not.mapped.com/resource.xml"
        base_uri, destination = desmap.find_destination(uri, "default/path")
        self.assertEqual("https://not.mapped.com", base_uri)
        self.assertEqual("./default/path", destination)

        #
        uri = "https://not.mapped.com/resource.xml"
        base_uri, destination = desmap.find_destination(uri, netloc=True)
        self.assertEqual("https://not.mapped.com", base_uri)
        self.assertEqual("./not.mapped.com", destination)

        desmap.set_root_folder("foo/bar")

        uri = "http://long.name.com/path/to/resource.xml"
        base_uri, destination = desmap.find_destination(uri)
        self.assertEqual("http://long.name.com", base_uri)
        self.assertEqual("foo/bar/destination1", destination)

    def test06_find_local_path(self):
        desmap = DestinationMap()

        desmap.__set_destination__("http://a.name.com/path/ignored", "local/folder/a")
        uri = "http://a.name.com/path/ignored/but/this/path/remains/file.txt"
        base_uri, local_path = desmap.find_local_path(uri)
        self.assertEqual("http://a.name.com/path/ignored", base_uri)
        self.assertEqual("./local/folder/a/but/this/path/remains/file.txt", local_path)

        desmap.__set_destination__("http://b.name.com/path/ignored/", "local/folder/b")
        uri = "http://b.name.com/path/ignored/but/this/path/remains/file.txt"
        base_uri, local_path = desmap.find_local_path(uri)
        self.assertEqual("http://b.name.com/path/ignored", base_uri)
        self.assertEqual("./local/folder/b/but/this/path/remains/file.txt", local_path)

        desmap.__set_destination__("http://c.name.com/path/ignored", "local/folder/c")
        uri = "http://c.name.com/path/ignored/but/this/path/remains/file.txt"
        base_uri, local_path = desmap.find_local_path(uri, infix="infix")
        self.assertEqual("http://c.name.com/path/ignored", base_uri)
        self.assertEqual("./local/folder/c/infix/but/this/path/remains/file.txt", local_path)







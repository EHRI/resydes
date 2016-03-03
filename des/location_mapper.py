#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, os.path
from urllib.parse import urlparse, urlunparse

MAP_FILENAME = "desmap.txt"


class DestinationMap(object):

    _map_filename = MAP_FILENAME

    @staticmethod
    def __get__logger():
        logger = logging.getLogger(__name__)
        return logger

    @staticmethod
    def _set_map_filename(map_filename):
        DestinationMap.__get__logger().info("Setting map_filenamee to %s", map_filename)
        DestinationMap._map_filename = map_filename

    @staticmethod
    def _get_map_filename():
        if not DestinationMap._map_filename:
            DestinationMap._set_map_filename(MAP_FILENAME)

        return DestinationMap._map_filename

    @staticmethod
    def shorten(uri):
        o = urlparse(uri)
        path = o.path
        new_path = os.path.dirname(path)
        if new_path == "/":
            new_path = ""
        new_uri = urlunparse((o.scheme, o.netloc, new_path, "", "", ""))
        return new_uri, new_path

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DestinationMap, cls).__new__(cls, *args, **kwargs)
            filename = DestinationMap._get_map_filename()
            DestinationMap.__get__logger().info("Creating DestinationMap._instance from %s" % filename)
            with open(filename) as file:
                lines = file.read().splitlines()

            DestinationMap.mappings = dict()
            for line in lines:
                k, v = line.split("=")
                DestinationMap.mappings[k] = v

            DestinationMap.__get__logger().info("Found %d entries in %s" % (len(DestinationMap.mappings), filename))

        return cls._instance

    def find_destination(self, uri, default_destination=None, netloc=False):
        s_uri = uri
        destination = None
        path = None
        while destination is None:
            try:
                destination = self.mappings[s_uri]
            except KeyError as err:
                if path == "":
                    break
                else:
                    (s_uri, path) = DestinationMap.shorten(s_uri)

        if destination is None:
            destination = default_destination

        if destination is None and netloc:
            destination = urlparse(uri).netloc

        return destination


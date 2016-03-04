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
        if DestinationMap._instance is None:
            DestinationMap.__get__logger().info("Setting map_filename to '%s'", map_filename)
            DestinationMap._map_filename = map_filename
        else:
            DestinationMap.__get__logger().warn("Setting map_filename on already initialized class. Using '%s'"
                                        % DestinationMap._get_map_filename())

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
            filename = DestinationMap._get_map_filename()
            DestinationMap.__get__logger().info("Creating DestinationMap._instance from '%s'" % filename)
            with open(filename) as file:
                lines = file.read().splitlines()

            DestinationMap.mappings = dict()
            for line in lines:
                if line.strip() == "" or line.startswith("#"):
                    pass
                else:
                    k, v = line.split("=")
                    DestinationMap.mappings[k] = v

            DestinationMap.__get__logger().info("Found %d entries in '%s'" % (len(DestinationMap.mappings), filename))
            cls._instance = super(DestinationMap, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def find_destination(self, uri, default_destination=None, netloc=False):
        s_uri = uri
        destination = None
        path = None
        while destination is None:
            try:
                destination = self.mappings[s_uri]
            except KeyError:
                if path == "":
                    break
                else:
                    (s_uri, path) = DestinationMap.shorten(s_uri)

        if destination is None:
            destination = default_destination

        if destination is None and netloc:
            destination = urlparse(uri).netloc

        return destination

    def __set_destination__(self, uri, destination):
        self.mappings[uri] = destination

    def __remove_destination__(self, uri):
        try:
            del self.mappings[uri]
        except KeyError:
            pass


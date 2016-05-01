#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, os.path, inspect
from urllib.parse import urlparse, urlunparse


class DestinationMap(object):
    """
    Singleton to map uri's to destinations on the local file system.
    To obtain the singleton instance call the constructor: DestinationMap()
    Prior to instantiating an instance, a map file may be set with the static method
    __set_map_filename__(map_filename). In order to force rereading of the map file, an instance may be dropped
    by calling __drop__() on the existing instance.


    DESTINATION MAPPING AT WORK

    The following schema shows destination mapping at work. In the map file a base uri is mapped to a destination:

        http://abcd.site.com/path/ignored=/data/resources/abcd

    All uri's that are extensions of the same base uri will be mapped to that destination.

    |------------ base uri -----------|
    |http://abcd.site.com/path/ignored/some/path/to/resource.ext
    |------------------------ full uri ------------------------|

    |---------- destination ----------|
    |             /data/resources/abcd/some/path/to/resource.ext
    |----------------------- local path -----------------------|

    Effectively the base uri will be replaced by destination.

    """

    _map_filename = None

    @staticmethod
    def __get__logger():
        logger = logging.getLogger(__name__)
        return logger

    @staticmethod
    def __set_map_filename__(map_filename):
        if DestinationMap._instance is None:
            DestinationMap.__get__logger().info("Setting map_filename to '%s'", map_filename)
            DestinationMap._map_filename = map_filename
        else:
            DestinationMap.__get__logger().warn("Setting map_filename on already initialized class. Using '%s'"
                                        % DestinationMap._get_map_filename())

    @staticmethod
    def _get_map_filename():
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
            DestinationMap.mappings = dict()
            if not filename is None:
                with open(filename) as file:
                    lines = file.read().splitlines()

                for line in lines:
                    if line.strip() == "" or line.startswith("#"):
                        pass
                    else:
                        k, v = line.split("=")
                        if k.endswith("/"):
                            k = k[:-1]
                        DestinationMap.mappings[k] = v

            cls.root_folder = "." # default
            DestinationMap.__get__logger().info("Found %d entries in '%s'" % (len(DestinationMap.mappings), filename))
            cls._instance = super(DestinationMap, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def __drop__(self):
        DestinationMap.__get__logger().debug("__drop__ %s called from [%s:%s]"
                    % (self.__class__.__name__, inspect.stack()[1][1], inspect.stack()[1][2]))
        DestinationMap._instance = None

    def set_root_folder(self, root_folder=None):
        if root_folder is None:
            self.root_folder = "."
        else:
            self.root_folder = root_folder

    def find_destination(self, uri, default_destination=None, netloc=False, infix=""):
        base_uri = uri
        destination = None
        path = None
        while destination is None:
            try:
                destination = self.mappings[base_uri]
            except KeyError:
                if path == "":
                    break
                else:
                    (base_uri, path) = DestinationMap.shorten(base_uri)

        if destination is None:
            destination = default_destination

        if destination is None and netloc:
            destination = urlparse(uri).netloc

        if destination is not None and not os.path.isabs(destination):
            destination = os.path.join(self.root_folder, destination)

        if destination is not None and infix != "":
            destination = os.path.join(destination, infix)

        return base_uri, destination

    def find_local_path(self, uri, default_destination=None, netloc=False, infix=""):
        base_uri = uri
        destination = None
        path = None
        postfix = None
        local_path = None
        while destination is None:
            try:
                destination = self.mappings[base_uri]
                postfix = uri[len(base_uri) + 1:]
            except KeyError:
                if path == "":
                    break
                else:
                    (base_uri, path) = DestinationMap.shorten(base_uri)

        if destination is None:
            destination = default_destination

        if destination is None and netloc:
            destination = urlparse(uri).netloc
            l = len(urlparse(uri).scheme) + len(destination)
            postfix = uri[l + 4:]

        if destination is not None and not os.path.isabs(destination):
            destination = os.path.join(self.root_folder, destination)

        if destination is not None and postfix is not None:
            local_path = os.path.join(destination, infix, postfix)

        return base_uri, local_path

    def __set_destination__(self, uri, destination):
        if uri.endswith("/"):
            uri = uri[:-1]
        self.mappings[uri] = destination

    def __remove_destination__(self, uri):
        if uri.endswith("/"):
            uri = uri[:-1]
        try:
            del self.mappings[uri]
        except KeyError:
            pass


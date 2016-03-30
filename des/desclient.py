#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, datetime, os.path, inspect, des.reporter
from resync.client import Client
from resync.mapper import Map
from des.config import Config


_instance = None


def instance():
    """
    resync.Client is a somewhat heavy class. Desclient inherits and is adapted to be used during one run of
    resyncing several sources. For convenience: grab the one instance from here.
    :return: an instance of Desclient
    """
    global _instance
    logger = logging.getLogger(__name__)
    if _instance is None:
        config = Config()

        # Parameters in the constructor of resync Client
        checksum = config.boolean_prop(Config.key_use_checksum, True)
        verbose = False

        # Parameters in the method client.baseline_or_audit
        audit_only = config.boolean_prop(Config.key_audit_only, True)
        dryrun = audit_only

        _instance = DesClient(checksum, verbose, dryrun)
        logger.debug("Created a new %s [checksum=%s, verbose=%s, dryrun=%s]"
                         % ( _instance.__class__.__name__ , checksum, verbose, dryrun))

    return _instance


def reset_instance():
    """
    Reset the _instance variable: next time an instance is requested it will be constructed anew.
    :return: None
    """
    global _instance
    _instance = None


class DesClient(Client):

    def __init__(self, checksum=False, verbose=False, dryrun=False):
        super().__init__(checksum, verbose, dryrun)
        self.logger = logging.getLogger(__name__)

    # The resync.client has a strict name convention: you can only give it a base url like
    #       "http://localhost:8000/rs/source/s1".
    # Calling 'baseline_or_audit' or 'incremental' on the original resync.client will then do so for the urls
    #       "http://localhost:8000/rs/source/s1/resourcelist.xml" and
    #       "http://localhost:8000/rs/source/s1/changelist.xml" respectively.
    # What if we have other file names for these resources: 'resourcelist_xyz.xml' or 'weird.foo'?
    # The two overrides below take away these name restrictions.
    #
    # Override name restriction
    def set_mappings(self, mappings):
        """Build and set Mapper object based on input mappings"""
        self.des_full_uri = mappings[0]     # i.e. http://localhost:8000/rs/source/s1/resourcelist_xyz.xml
        self.des_destination = mappings[1]  # i.e. rs/destination/d1

        uri = os.path.dirname(self.des_full_uri)
        super().set_mappings((uri, self.des_destination))

    # Override name restriction
    def sitemap_uri(self, basename):
        """Get full URI (filepath) for sitemap based on basename"""
        return self.des_full_uri

    # Override
    def log_status(self, in_sync=None, incremental=False, audit=False,
                   same=None, created=0, updated=0, deleted=0, to_delete=0, exception=None):
        origin = "%s:%s" % (inspect.stack()[1][1], inspect.stack()[1][2])
        des.reporter.instance().log_status(self.mapper.default_src_uri(), origin, in_sync, incremental, audit, same,
                                           created, updated, deleted, to_delete, exception)
        super().log_status(in_sync, incremental, audit, same, created, updated, deleted, to_delete)









# class DesMapper(object):
#     """
#     Replacement of resync.mapper.Mapper
#     """
#     def __init__(self, uri, destination):
#         self.logger = logging.getLogger(__name__)
#         self.src_uri = uri
#         self.destination = destination
#         self.mappings = []
#         map = Map(uri, destination)
#         self.mappings.append(map)
#
#
#     def __len__(self):
#         """Length is number of mappings"""
#         self.logger.debug("DesMapper.__len__ from [%s:%s]" % (inspect.stack()[1][1], inspect.stack()[1][2]))
#         return 1
#
#     def default_src_uri(self):
#         """Default src_uri from mapping
#
#         This is take just to be the src_uri of the first entry
#         """
#         self.logger.debug("DesMapper.default_src_uri from [%s:%s]" % (inspect.stack()[1][1], inspect.stack()[1][2]))
#         return self.src_uri
#
#     def unsafe(self):
#         """True is one or more mapping is unsafe
#
#         See Map.unsafe() for logic. Provide this as a test rather than
#         building into object creation/parse because it is useful to
#         allow unsafe mappings in situations where it doesn't matter.
#         """
#         self.logger.debug("DesMapper.unseafe from [%s:%s]" % (inspect.stack()[1][1], inspect.stack()[1][2]))
#         return False
#
#     def dst_to_src(self, dst_file):
#         """Map destination path to source URI"""
#         self.logger.debug("DesMapper.dst_to_src(%s) from [%s:%s]" % (dst_file, inspect.stack()[1][1], inspect.stack()[1][2]))
#         # dst_file              rs/destination/d1/files/resource1.txt
#         # return http:localhost:8000/rs/source/s1/files/resource1.txt
#
#         #return self.src_uri  # or ? return "http://localhost:8000/rs/source/s1"
#         if dst_file.endswith("resource1.txt"):
#             return "http:localhost:8000/rs/source/s1/files/resource1.txt"
#         else:
#             return "http:localhost:8000/rs/source/s1/files/resource2.txt"
#
#
#     def src_to_dst(self, uri):
#         """Map source URI to destination path"""
#         self.logger.debug("DesMapper.src_to_dst(%s) from [%s:%s]" % (uri, inspect.stack()[1][1], inspect.stack()[1][2]))
#
#         common_prefix = os.path.commonprefix([self.src_uri, uri])
#         rel_path = os.path.relpath(uri, common_prefix)
#         filename = os.path.join(self.destination, rel_path)
#
#         self.logger.debug("DesMapper returns '%s'" % filename)
#         return filename
#
#     def path_from_uri(self, uri):
#         """Make a safe path name from uri
#
#         In the case that uri is already a local path then the same path
#         is returned.
#         """
#         self.logger.debug("DesMapper.path_from_uri(%s) from [%s:%s]" % (uri, inspect.stack()[1][1], inspect.stack()[1][2]))
#         raise NotImplementedError
#
#     def __repr__(self):
#         self.logger.debug("DesMapper.__repr__ from [%s:%s]" % (inspect.stack()[1][1], inspect.stack()[1][2]))
#         return self.src_uri + " >> " + self.destination
#

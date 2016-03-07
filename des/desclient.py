#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, datetime, os.path, inspect
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
        self.sync_status = []
        self.mapper = None

    # def set_mappings(self, uri, destination):
    #     self.mapper = DesMapper(uri, destination)

    # @property
    # def sitemap(self):
    #     """Return the sitemap URI based on maps or explicit settings"""
    #     if self.mapper is None:
    #         raise UnboundLocalError("No mappings set.")
    #     return self.mapper.src_uri

    # Override
    # def sitemap_uri(self, basename):
    #     """
    #     Whatever the super class of this is trying to do in this method, we don't want to end up with uri's like
    #     http://whatever.com/path/resourcelist.xml/resourcelist.xml
    #     :param basename:
    #     :return: The initial uri (i.e. http://whatever.com/path/resourcelist.xml)
    #     """
    #     return self.mapper.default_src_uri()

    # # Duck type:
    # def uri_to_destination(self, uri):
    #     # uri is  something like 'http://localhost:8000/rs/source/s1/files/resource1.txt'
    #     # src_uri something like 'http://localhost:8000/rs/source/s1/resourcelist.xml'
    #     # Destination is                           rs/destination/d1
    #     # filename should be                       rs/destination/d1/files/resource1.txt'
    #     raise NotImplementedError
    #     src_uri = self.mapper.mappings[0].src_uri
    #     destination = self.mapper.mappings[0].dst_path
    #
    #     common_prefix = os.path.commonprefix([src_uri, uri])
    #     rel_path = os.path.relpath(uri, common_prefix)
    #     filename = os.path.join(destination, rel_path)
    #
    #     self.logger.debug("Duck type: sub called from super and returns '%s'" % filename)
    #     return filename

    # Override
    def log_status(self, in_sync=None, incremental=False, audit=False,
                   same=None, created=0, updated=0, deleted=0, to_delete=0, exception=None):
        self.sync_status.append(SourceStatus(self.mapper.default_src_uri(), in_sync, incremental, audit, same,
                                             created, updated, deleted, to_delete, exception))
        super().log_status(in_sync, incremental, audit, same, created, updated, deleted, to_delete)

    def sync_status_to_file(self, filename):
        with open(filename, 'w') as file:
            file.write("%s\n" % "date,uri,in_sync,incremental,audit,same,created,updated,deleted,to_delete,exception")
            for item in self.sync_status:
                file.write("%s\n" % item)
            file.close()
        self.logger.info("Wrote audit file %s" % filename)


class SourceStatus(object):

    def __init__(self, uri, in_sync, incremental, audit, same, created, updated, deleted, to_delete, exception):
        self.datetime = datetime.datetime.now()
        self.uri = uri
        self.in_sync = in_sync
        self.incremental = incremental
        self.audit = audit
        self.same = same
        self.created = created
        self.updated = updated
        self.deleted = deleted
        self.to_delete = to_delete
        self.exception = exception

    def __str__(self):
        s = "\""
        s += str(self.datetime)
        s += "\",\""
        s += self.uri
        s += "\",\""
        s += str(self.in_sync)
        s += "\",\""
        s += str(self.incremental)
        s += "\",\""
        s += str(self.audit)
        s += "\",\""
        s += str(self.same)
        s += "\",\""
        s += str(self.created)
        s += "\",\""
        s += str(self.updated)
        s += "\",\""
        s += str(self.deleted)
        s += "\",\""
        s += str(self.to_delete)
        s += "\",\""
        s += str(self.exception)
        s += "\""
        return s


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

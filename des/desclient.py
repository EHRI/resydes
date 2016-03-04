#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, datetime
from resync.client import Client
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
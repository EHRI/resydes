#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, datetime, inspect
from des.config import Config

_instance = None


def instance():
    global _instance
    if _instance is None:
        _instance = Reporter()

    return _instance


def reset_instance():
    global _instance
    _instance = None


class Reporter(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Creating new %s" % self.__class__.__name__)
        self.sync_status = []

    def log_status(self, uri, origin=None, in_sync=None, incremental=False, audit=False,
                   same=None, created=0, updated=0, deleted=0, to_delete=0, exception=None):
        if origin is None:
            origin = "%s:%s" % (inspect.stack()[1][1], inspect.stack()[1][2])
        self.sync_status.append(SourceStatus(uri, origin, in_sync, incremental, audit, same,
                                             created, updated, deleted, to_delete, exception))

    def sync_status_to_file(self, filename=None):
        if filename is None:
            filename = Config().prop(Config.key_sync_status_report_file, "sync-status.csv")
        with open(filename, 'w') as file:
            file.write("%s\n" % "date,uri,in_sync,incremental,audit,same,created,updated,deleted,to_delete,exception,origin")
            for item in self.sync_status:
                file.write("%s\n" % item)
            file.close()
        self.logger.info("Wrote %d source statuses to audit file %s" % (len(self.sync_status), filename))

    def sync_status_to_string(self):
        s = ""
        for item in self.sync_status:
            s = s + str(item) + "\n"
        return s



class SourceStatus(object):

    def __init__(self, uri, origin, in_sync, incremental, audit, same, created, updated, deleted, to_delete, exception):
        self.datetime = datetime.datetime.now()
        self.uri = uri
        self.origin = origin
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
        s += "\",\""
        s += self.origin
        s += "\""
        return s




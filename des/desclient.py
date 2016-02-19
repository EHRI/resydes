#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from resync.client import Client

class DesClient(Client):

    def __init__(self, checksum=False, verbose=False, dryrun=False):
        super().__init__(checksum, verbose, dryrun)
        self.logger = logging.getLogger(__name__)
        self.sync_status = []

    def log_status(self, in_sync=True, incremental=False, audit=False,
                   same=None, created=0, updated=0, deleted=0, to_delete=0):
        self.sync_status.append(SourceStatus(self.mapper.default_src_uri(), in_sync, incremental, audit, same,
                                             created, updated, deleted, to_delete))
        super().log_status(in_sync, incremental, audit, same, created, updated, deleted, to_delete)

    def sync_status_to_file(self, filename):
        with open(filename, 'w') as file:
            file.write("%s\n" % "uri,in_sync,incremental,audit,same,created,updated,deleted,to_delete")
            for item in self.sync_status:
                file.write("%s\n" % item)
            file.close()
        self.logger.info("Wrote audit file %s" % filename)


class SourceStatus(object):

    def __init__(self, uri, in_sync, incremental, audit, same, created, updated, deleted, to_delete):
        self.uri = uri
        self.in_sync = in_sync
        self.incremental = incremental
        self.audit = audit
        self.same = same
        self.created = created
        self.updated = updated
        self.deleted = deleted
        self.to_delete = to_delete

    def __str__(self):
        s = "\""
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
        s += "\""
        return s
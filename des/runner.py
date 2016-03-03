#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# 1. Baseline synchronization
# 2. Incremental synchronization
# 3. Audit
#

import logging
from des.desclient import DesClient
from resync.client import ClientFatalError


class Runner(object):

    def __init__(self, mappings=[]):
        '''
        Create a Runner object that will act on the given mappings.
        :param mappings: A lot of things. To keep things simple: a list of key-value pairs of the format
                url=destination_folder
                http://institution.with.resync.com/resync/dir/=/path/to/destination/folder/for/this/particular/source
        :return: None
        '''
        self.logger = logging.getLogger(__name__)
        self.mappings = mappings

    def read_mappings(self, filename):
        """
        Read the mappings from a file. Lines in the file have format url=destination_folder
        :param filename: the name of the file
        :return: None
        """
        with open(filename) as file:
            self.mappings = file.read().splitlines()

    def run_audit(self):
        """
        Run an audit on the sources that are present in the mappings of this Runner.
        :return: the desclient.DesClient used to do the audit with, giving the sync status of the sources
        """
        return self.run_baseline_or_audit(dryrun=True)

    def run_baseline(self):
        """
        Run a baseline synchronisation on the sources that are present in the mappings of this Runner.
        :return: the desclient.DesClient used to do the baseline with, giving the sync status of the sources
        """
        return self.run_baseline_or_audit(dryrun=False)

    def run_baseline_or_audit(self, dryrun=True):
        '''
        Do a baseline or audit on the sources in the mappings of this Runner.

        :param dryrun: if True: resources will not be deleted or updated,
                       if False: resources will be deleted or updated in order to mirror the source state
        :return: the desclient.DesClient used to do the baseline or audit with, giving the sync status of the sources
        '''
        # FINDING OUT what is the meaning and effect of parameters in the constructor of resync Client.
        #
        # the boolean parameter 'checksum' in the constructor of Client is given to ResourceListBuilder.
        # What side effects it has on baseline or audit is unclear. It is tempered with by each run of
        # Client.baseline_or_audit and Client.incremental.
        checksum = True
        #
        # the boolean parameter 'verbose' in the constructor of client is -apparently- only used in
        # the methods parse_document and read_reference_resourcelist and has the effect of printing
        # stuff. We do not want stuff to be printed.
        verbose = False
        #
        # the boolean parameter 'dryrun', if True, has the effect that it will only log what would happen
        # in the methods client.delete_resource and client.update_resource
        #
        # FINDING OUT what is the meaning and/or effect of parameters in the method client.baseline_or_audit
        #
        # allow_deletion: same as dryrun with obvious opposite boolean.
        allow_deletion = not dryrun
        #
        # audit_only: same as dryrun.
        audit_only = dryrun
        #
        # For logging: what excactly are we doing
        action = "AUDIT-BASELINE" if dryrun else "BASELINE"

        self.logger.info("Start baseline_or_audit. #mappings=%s dryrun=%s", len(self.mappings), dryrun)

        desclient = DesClient(checksum, verbose, dryrun)
        # The client only ever does the first of the mappings so why is the mappings a list?
        # Split out the mappings in individual ones and do the baseline or audit on each.
        for map in self.mappings:
            self.logger.info("%s on %s" % (action, map))
            try:
                map = ("file:///Users/ecco/git/resydes/des/test/rs/source/s1", "/Users/ecco/git/resydes/des/test/rs/destination/d1")
                desclient.set_mappings(map)
                #desclient.set_mappings([map])
                desclient.baseline_or_audit(allow_deletion, audit_only)
            except ClientFatalError as err:
                self.logger.warn("%s-EXCEPTION while syncing %s" % (action, map), exc_info=True)
                desclient.log_status(exception=err)
            finally:
                # Whether or not the resourcelist just processed had checksums influences the state of the
                # class-level property Client.checksum. Make sure it is always set to True before the next
                # source is processed.
                desclient.checksum = checksum

        return desclient

    def run_incremental(self, dryrun=True):
        """
        Do synchronisation with changelists.

        :param dryrun: if True: resources will not be deleted or updated,
                       if False: resources will be deleted or updated in order to mirror the source state
        :return: the desclient.DesClient used to do the incremental with, giving the sync status of the sources
        """
        # FINDING OUT what is the meaning and effect of parameters in the constructor of resync Client.
        #
        # the boolean parameter 'checksum' in the constructor of Client is given to ResourceListBuilder.
        # What side effects it has on incremental is unclear. It is tempered with by each run of
        # Client.baseline_or_audit and Client.incremental.
        # checksum [cannot] could not be other than False, because True generates the error
        # AttributeError: 'ChangeList' object has no attribute 'has_md5'
        # ChangeList now has the attribute 'has_md5'.
        checksum = True
        #
        # the boolean parameter 'verbose' in the constructor of client is -apparently- only used in
        # the methods parse_document and read_reference_resourcelist and has the effect of printing
        # stuff. We do not want stuff to be printed.
        verbose = False
        #
        # the boolean parameter 'dryrun', if True, has the effect that it will only log what would happen
        # in the methods client.delete_resource and client.update_resource
        #
        # FINDING OUT what is the meaning and/or effect of parameters in the method client.incremental
        #
        # allow_deletion: same as dryrun with obvious opposite boolean.
        allow_deletion = not dryrun
        #
        # change_list_uri: Is this the name given to a source-local changelist.xml? Let's default.
        change_list_uri = None
        #
        # from_datetime: The datetime of last sync. If we always do a baseline before an incremental will we have
        # the value of this parameter in the file .resync-cient-status.cfg?
        from_datetime = None
        #
        # For logging: what excactly are we doing
        action = "AUDIT-INCREMENTAL" if dryrun else "INCREMENTAL"

        self.logger.info("Start incremental. #mappings=%s dryrun=%s", len(self.mappings), dryrun)

        desclient = DesClient(checksum, verbose, dryrun)

        for map in self.mappings:
            self.logger.info("%s on %s" % (action, map))
            try:
                desclient.set_mappings([map])
                desclient.incremental(allow_deletion=allow_deletion, change_list_uri=change_list_uri, from_datetime=from_datetime)
            except ClientFatalError as err:
                self.logger.warn("%s-EXCEPTION while syncing %s" % (action, map), exc_info=True)
                desclient.log_status(incremental=True, exception=err)

        return desclient

    def run_explore(self):
        checksum = True
        verbose = False
        dryrun = True

        desclient = DesClient(checksum, verbose, dryrun)
        desclient.set_mappings(self.mappings)
        desclient.explore()

        return desclient

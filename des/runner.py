#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# 1. Baseline synchronization
# 2. Incremental synchronization
# 3. Audit
# are the 3 fundamental steps in resource synchronization. It would be nice if the destination system can figure out
# by it self what it has to do, given a list of URI's against which to synchronize.
#

import logging
from des.desclient import DesClient

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

    def run_baseline_or_audit(self, dryrun = True):
        '''
        Do a baseline or audit on the sources in the mappings of this Runner.

        :param dryrun: if True: resources will not be deleted or updated,
                       if False: resources will be deleted or updated in order to mirror the source state
        :return: the desclient.DesClient used to do the baseline or audit with, giving the sync status of the sources
        '''
        # FINDING OUT what is the meaning and effect of parameters in the constructor of resync Client.
        #
        # the boolean parameter 'checksum' in the constructor of Client is given to ResourceListBuilder.
        # What side effects it has on baseline or audit is unclear.
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
        self.logger.info("Start baseline_or_audit. #mappings=%s dryrun=%s", len(self.mappings), dryrun)

        client = DesClient(checksum, verbose, dryrun)
        # The client only ever does the first of the mappings so why is the mappings a list?
        # Split out the mappings in individual ones and do the baseline or audit on each.
        for map in self.mappings:
            self.logger.info("Audit or baseline on %s", map)
            client.set_mappings([map])
            client.baseline_or_audit(allow_deletion, audit_only)

        return client

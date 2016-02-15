#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# 1. Baseline synchronization
# 2. Incremental synchronization
# 3. Audit
# are the 3 fundamental steps in resource synchronization. It would be nice if the destination system can figure out
# by it self what it has to do, given a list of URI's against which to synchronize.
#

import logging
from resync.client import Client, ClientFatalError

logger = logging.getLogger("")


class Runner(object):

    def __init__(self, mappings=[]):
        '''
        Create a Runner object that will act on the given mappings.
        :param mappings: A lot of things. To keep things simple: a list of key-value pairs of the format
                url=destination_folder
                http://institution.with.resync.com/resync/dir/=/path/to/destination/folder/for/this/particular/source
        :return: None
        '''
        self.mappings = mappings
        logger.debug("Created new Runner with %d mappings.", len(mappings))

    def run_baseline_or_audit(self, dryrun = True):
        '''
        Do a baseline or audit on the sources in the mappings of this Runner.
        :param dryrun: if True: resources will not be deleted or updated,
                       if False: resources will be deleted or updated in order to mirror the source state
        :return: None
        '''
        # FINDING OUT what is the meaning and effect of parameters in the constructor of resync Client.
        #
        # the boolean parameter 'checksum' in the constructor of Client is -apparently- only given to
        # ResourceListBuilder, so will not be needed when using client as destination (?)
        checksum = False
        #
        # the boolean parameter 'verbose' in the constructor of client is -apparently- only used in
        # the methods parse_document and read_reference_resourcelist and has the effect of printing
        # stuff. We do not want stuff to be printed.
        verbose = False
        #
        # the boolean parameter 'dryrun', if True, has the effect that it will only log what would happen
        # in the methods delete_resource and update_resource
        #
        self.client = Client(checksum, verbose, dryrun)
        self.client.set_mappings(self.mappings)
        # FINDING OUT what is the meaning and/or effect of parameters in the method client.baseline_or_audit
        #
        # allow_deletion: same as dryrun with obvious opposite boolean.
        allow_deletion = not dryrun
        #
        # audit_only: same as dryrun.
        audit_only = dryrun
        #
        logger.debug("Start baseline_or_audit. dryrun=%s", dryrun)
        # try:
        #     self.client.baseline_or_audit(allow_deletion, audit_only)
        # except ClientFatalError as err:
        #     logger.error(err)

        self.client.baseline_or_audit(allow_deletion, audit_only)

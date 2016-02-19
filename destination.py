#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, logging.config
from resync.client import Client, ClientFatalError

logging.config.fileConfig('logging.conf')

logger = logging.getLogger(__name__)

class Destination(object):

    def __init__(self):
        logger.info("Starting a new Destination")


    def baseline(self):
        checksum=False
        verbose=False
        dryrun=False

        c = Client(checksum, verbose, dryrun)

        mappings = ["http://zandbak11.dans.knaw.nl/shiny/resy/=/Users/ecco/tmp/resy",
                    "file:///Users/ecco/git/resydes/des/test/rs/source/s2/files/=/Users/ecco/tmp/rs"]
        c.set_mappings(mappings)

        allow_deletion = False
        audit_only = False

        try:
            c.baseline_or_audit(allow_deletion, audit_only)
        except ClientFatalError as err:
            print("Oeps: " + str(err))
        print("finished")

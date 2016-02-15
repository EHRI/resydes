#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest, logging, logging.config
from des.runner import Runner

logging.config.fileConfig('logging.conf')

logger = logging.getLogger(__name__)

class TestRunner(unittest.TestCase):

    def test01_baseline_or_audit(self):
        logger.debug("Starting test")
        runner = Runner()
        runner.run_baseline_or_audit()

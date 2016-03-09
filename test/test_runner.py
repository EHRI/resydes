#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import logging.config
import unittest

from runner import Runner

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


class TestRunner(unittest.TestCase):

    def test01__init__(self):
        with self.assertRaises(FileNotFoundError):
            Runner()




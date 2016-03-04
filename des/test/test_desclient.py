#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest, logging, logging.config, des.desclient
from des.config import Config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

class TestDesClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Config._set_config_filename("test-files/config.txt")

    def test01_instance(self):
        desclient1 = des.desclient.instance()
        self.assertIsNotNone(desclient1)

        desclient2 = des.desclient.instance()
        self.assertEqual(desclient1, desclient2)

        des.desclient.reset_instance()
        desclient3 = des.desclient.instance()
        self.assertIsNotNone(desclient3)
        self.assertNotEqual(desclient1, desclient3)



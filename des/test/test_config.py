#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest, logging, logging.config

from des.config import Config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


class TestConfig(unittest.TestCase):

    def test01_new(self):
        Config._set_config_filename("test-files/no-config.txt")

        with self.assertRaises(FileNotFoundError):
            Config()

    def test02_new(self):
        Config._set_config_filename("test-files/config.txt")
        config = Config()
        self.assertEqual("test-files/config.txt", config._config_filename)
        self.assertEqual("test-files/config.txt", Config._get_config_filename())

        self.assertEqual("logging.conf", config.prop(Config.key_logging_configuration_file))
        self.assertEqual("test-files/desmap.txt", config.prop(Config.key_location_mapper_destination_file))

    def test03_boolean_prop(self):
        Config._set_config_filename("test-files/config.txt")
        config = Config()

        self.assertFalse(config.boolean_prop(Config.key_use_netloc))

        config.__set_prop__(Config.key_use_netloc, str(True))
        self.assertTrue(config.boolean_prop(Config.key_use_netloc))

        config.__set_prop__(Config.key_use_netloc, str(False))
        self.assertFalse(config.boolean_prop(Config.key_use_netloc))

        self.assertTrue(config.boolean_prop("no_key", True))
        self.assertFalse(config.boolean_prop("no_key", False))


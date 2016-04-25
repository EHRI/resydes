#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest, logging, logging.config

from des.config import Config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


class TestConfig(unittest.TestCase):

    def setUp(self):
        Config._set_config_filename("test-files/config.txt")
        Config().__drop__()

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

    def test04_list_prop(self):
        Config._set_config_filename("test-files/config.txt")
        config = Config()

        list = config.list_prop("test_list")
        self.assertEqual(3, len(list))
        self.assertEqual("foo.bar", list[0])
        self.assertEqual("bar.foo", list[1])
        self.assertEqual("foo.bar.baz", list[2])

    def test04__drop__(self):
        Config._set_config_filename("test-files/config.txt")
        config1 = Config()

        self.assertIsNotNone(config1)
        self.assertIsNone(config1.prop("this_is"))
        config1.__drop__()
        self.assertIsNone(Config._instance)

        Config._set_config_filename("test-files/alt-config.txt")
        config2 = Config()
        self.assertIsNotNone(config2)
        self.assertNotEqual(config1, config2)
        self.assertEqual("a_test", config2.prop("this_is"))
        config2.__drop__()


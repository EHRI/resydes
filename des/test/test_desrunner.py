#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest, des.processor
from des.desrunner import DesRunner
from des.config import Config

class TestDesrunner(unittest.TestCase):

    @unittest.skip("real live test")
    def test_practical(self):
        config = "/Users/ecco/APPS/resydes/resydes/conf2/config.txt"
        sources = "/Users/ecco/APPS/resydes/sources.txt"
        task = "discover"
        once = True

        runner = DesRunner(config_filename=config)
        runner.run(sources, task, once)

    def test_inject_dependencies(self):
        Config.__set_config_filename__("test-files/config.txt")
        Config().__set_prop__(Config.key_des_processor_listeners,
                              "des.processor_listener.SitemapWriter, des.processor.ProcessorListener")

        runner = DesRunner()
        self.assertEqual(2, len(des.processor.processor_listeners))


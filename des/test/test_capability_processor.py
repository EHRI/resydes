#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest, logging, logging.config, threading
from des.capability_processor import Capaproc


logging.config.fileConfig('logging.conf')

logger = logging.getLogger(__name__)


class TestCapaproc(unittest.TestCase):

    def test01__init__(self):
        # with no parameters
        capaproc = Capaproc()





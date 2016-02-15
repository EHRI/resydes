#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest
import logging
from destination import Destination

class TestDestination(unittest.TestCase):

    def test01_baseline(self):

        d = Destination()
        d.baseline()
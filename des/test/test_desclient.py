#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from des.desclient import DesClient

class TestDesClient(unittest.TestCase):

    def test01_create(self):
        dc = DesClient()


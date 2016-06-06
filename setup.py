#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(name='resydes',
      version='0.1.0',
      description='Resource Sync Destination',
      long_description='''
        Basic implementation of a Resource Sync Destination.
      ''',
      author='henk van den berg',
      author_email='henk.van.den.berg@dans.knaw.nl',
      url='https://github.com/EHRI/resydes',
      packages=['des'],
      install_requires=['requests'],
      # configuration files are injected at start up of desrunner
      # data_files=[('/conf', ['conf/config.txt', 'conf/desmap.txt', 'conf/logging.conf']),
      #             #('logs', ['']),
      #             #('', ['README.md'])
      # ],
      # dependency_links=['https://github.com/EHRI/resync/archive/ehribranch.zip'],
      # install_requires=[
      #     'resync',
      # ],
     )

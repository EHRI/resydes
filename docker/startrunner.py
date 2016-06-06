#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from des.desrunner import DesRunner


task_choices = ['discover', 'wellknown', 'capability']
parser = argparse.ArgumentParser(description="Run a ResourceSync Destination.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-s", "--sources", help="the name of the file with source urls", default="conf/sources.txt")
parser.add_argument("-c", "--config", help="the configuration filename", default="conf/config.txt", metavar="")
parser.add_argument("-t", "--task", help="the task that should be run. " + str(task_choices), default="discover",
                        choices=task_choices, metavar="")
parser.add_argument("-o", "--once", help="explore source urls once and exit", action="store_true")

args = parser.parse_args()

runner = DesRunner(config_filename=args.config)
runner.run(args.sources, args.task, args.once)


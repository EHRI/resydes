#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# 1. Baseline synchronization
# 2. Incremental synchronization
# 3. Audit
#

import sys, argparse, os.path, logging, logging.config, time
sys.path.append(".")
try:
    sys.path.insert(0, "../resync")
except:
    pass

import des.reporter
from des.config import Config
from des.location_mapper import DestinationMap
from des.processor import Sodesproc, Capaproc
from des.discover import Discoverer


class DesRunner(object):

    def __init__(self, config_filename="conf/config.txt"):
        '''
        Create a Runner using the configuration file denoted by config_filename.
        :param config_filename:
        :return: None
        '''
        try:
            Config._set_config_filename(config_filename)
            config = Config()

        except FileNotFoundError as err:
            print(err)
            raise err

        logging_configuration_file = config.prop(Config.key_logging_configuration_file, "conf/logging.conf")
        # logging.config.fileConfig raises "KeyError: 'formatters'" if the configuration file does not exist.
        # A FileNotFoundError in this case is less confusing.
        if not os.path.isfile(logging_configuration_file):
            # It seems there is no default logging configuration to the console in Python?
            # In that case we'll call it a day.
            raise FileNotFoundError("Logging configuration file not found: " + logging_configuration_file)

        logging.config.fileConfig(logging_configuration_file)
        self.logger = logging.getLogger(__name__)

        self.pid = os.getpid()
        self.sources = None
        self.exceptions = []

        self.logger.info("Started %s with pid %d" % (__file__, self.pid))
        self.logger.info("Configured %s from '%s'" % (self.__class__.__name__, config_filename))
        self.logger.info("Configured logging from '%s'" % logging_configuration_file)

    def run(self, sources, task="discover", once=False):
        condition = True
        while condition:
            # list of urls
            self.logger.info("Reading source urls from '%s'" % sources)
            self.read_sources_doc(sources)
            # reset url --> destination map. New mappings may be configured
            DestinationMap._set_map_filename(Config().
                                             prop(Config.key_location_mapper_destination_file, "conf/desmap.txt"))
            # drop to force fresh read from file
            DestinationMap().__drop__()
            # Set the root of the destination folder if configured
            DestinationMap().set_root_folder(Config().prop(Config.key_destination_root))
            # do all the urls
            self.do_task(task)
            # report
            self.do_report(task)
            # to continue or not to continue
            condition = not (once or self.stop())
            if condition:
                pause = Config().int_prop(Config.key_sync_pause)
                self.logger.info("Going to sleep for %d seconds." % pause)
                self.logger.info("command line: 'touch stop' to stop this process with pid %d." % self.pid)
                time.sleep(pause)
                # repeat after sleep
                condition = not (once or self.stop())

    def read_sources_doc(self, sources):
        with open(sources) as f:
            lines = f.read().splitlines()
        self.sources = []
        for line in lines:
            if line.strip() == "" or line.startswith("#"):
                pass
            else:
                self.sources.append(line)
        self.logger.info("Got %d source urls from '%s'" % (len(self.sources), sources))

    def do_task(self, task):
        for uri in self.sources:
            processor = None
            if task == "discover":
                discoverer = Discoverer(uri)
                processor = discoverer.get_processor()
            elif task == "wellknown":
                processor = Sodesproc(uri)
            elif task == "capability":
                processor = Capaproc(uri)

            if processor is None:
                msg = "Could not discover processor for '%s'" % uri
                self.logger.warn(msg)
                self.exceptions.append(msg)
                des.reporter.instance().log_status(uri, exception=msg)
            else:
                try:
                    processor.process_source()
                    self.exceptions.extend(processor.exceptions)
                    # do something with processor status
                except Exception as err:
                    self.exceptions.append(err)
                    self.logger.warn("Failure while syncing %s" % uri, exc_info=True)
                    des.reporter.instance().log_status(uri, exception=err)

    def do_report(self, task):
        reporter = des.reporter.instance()
        reporter.sync_status_to_file()
        # reset used reporter
        des.reporter.reset_instance()
        self.logger.info("Ran task '%s' over %d sources with %d exceptions" % (task, len(self.sources), len(self.exceptions)))
        self.exceptions = []

    def stop(self):
        stop = os.path.isfile("stop")
        if stop:
            self.logger.info("Stopping %s because found file named 'stop'" % self.__class__.__name__)

        return stop


if __name__ == '__main__':
    # Run a DesRunner instance
    task_choices = ['discover', 'wellknown', 'capability']

    parser = argparse.ArgumentParser(description="Run a ResourceSync Destination.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("sources", help="the name of the file with source urls")
    parser.add_argument("-c", "--config", help="the configuration filename", default="conf/config.txt", metavar="")
    parser.add_argument("-t", "--task", help="the task that should be run. " + str(task_choices), default="discover",
                        choices=task_choices, metavar="")
    parser.add_argument("-o", "--once", help="explore source urls once and exit", action="store_true")

    args = parser.parse_args()

    runner = DesRunner(config_filename=args.config)
    runner.run(args.sources, args.task, args.once)


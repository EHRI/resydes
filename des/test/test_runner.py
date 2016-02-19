#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest, logging, logging.config, os.path, pathlib, glob, shutil
from des.runner import Runner
from resync.client import Client, ClientFatalError
from urllib.parse import urljoin

logging.config.fileConfig('logging.conf')

logger = logging.getLogger(__name__)

class TestRunner(unittest.TestCase):

    def __create_mappings__(self):
        """
        creates the mapping between the source and the destination folder like [source=destination]
        [
            'file:///Users/ecco/git/resydes/des/test/rs/source/s1=/Users/ecco/git/resydes/des/test/rs/destination/d1',
            'file:///Users/ecco/git/resydes/des/test/rs/source/s2=/Users/ecco/git/resydes/des/test/rs/destination/d2'
        ]
        :return: a list with mappings between sources and destinations.
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))

        path_s1 = os.path.join(abs_path, "rs/source/s1")
        s1 = pathlib.Path(path_s1).as_uri()
        path_s2 = os.path.join(abs_path, "rs/source/s2")
        s2 = pathlib.Path(path_s2).as_uri()

        d1 = os.path.join(abs_path, "rs/destination/d1")
        d2 = os.path.join(abs_path, "rs/destination/d2")

        mappings = [s1 + "=" + d1, s2 + "=" + d2]
        return mappings

    def __clear_sources_xml__(self):
        """
        remove all xml files from source subfolders s1 and s2
        :return:
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        s1 = os.path.join(abs_path, "rs/source/s1/*.xml")
        s2 = os.path.join(abs_path, "rs/source/s2/*.xml")
        files = glob.glob(s1)
        for f in files:
            os.remove(f)
        files = glob.glob(s2)
        for f in files:
            os.remove(f)

    def __clear_destination__(self):
        """
        remove all files from destination subfolders d1 and d2.
        :return:
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        d1_files = os.path.join(abs_path, "rs/destination/d1/files")
        d2_files = os.path.join(abs_path, "rs/destination/d2/files")
        shutil.rmtree(d1_files, ignore_errors=True)
        shutil.rmtree(d2_files, ignore_errors=True)


    def __create_resourcelist__(self, src):
        """
        Create a resourcelist xml for the source denominated by out.
        :param src: either 's1' or 's2'
        :return:
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        data = [os.path.join(abs_path, "rs/source", src, "files/resource1.txt"),
                os.path.join(abs_path, "rs/source", src, "files/resource2.txt")]
        paths = ",".join(data)
        #logger.debug("paths is a string '%s'", paths)
        outfile = os.path.join(abs_path, "rs/source", src, "resourcelist.xml")

        # create a resourcelist from the files in test/rs/files
        client = Client(checksum=True)

        prefix_path = os.path.join(abs_path, "rs/source", src, "files")
        prefix = pathlib.Path(prefix_path).as_uri()
        resourcedir = os.path.join(abs_path, "rs/source", src, "files")
        args = [prefix, resourcedir]

        client.set_mappings(args)
        client.write_resource_list(paths, outfile)

    def test01_baseline_or_audit(self):
        # no mappings
        #logger.debug("Starting tests")
        runner = Runner()
        client = runner.run_baseline_or_audit()
        self.assertEqual(0, len(client.sync_status))

    def test02_baseline_or_audit(self):
        # still no mappings
        runner = Runner()
        client = runner.run_baseline_or_audit(dryrun=False)
        self.assertEqual(0, len(client.sync_status))

    def test03_baseline_or_audit(self):
        # no resourcelist.xml
        self.__clear_sources_xml__()
        runner = Runner(self.__create_mappings__())
        self.assertRaises(ClientFatalError, runner.run_baseline_or_audit, dryrun=True)

    def test04_run_audit(self):
        # do an audit on the 2 sources in the mappings
        self.__clear_sources_xml__()
        self.__create_resourcelist__("s1")
        self.__create_resourcelist__("s2")
        self.__clear_destination__()
        mappings = self.__create_mappings__()
        logger.debug("\n=================\n")

        runner = Runner(mappings)
        client = runner.run_audit()

        self.assertEqual(2, len(client.sync_status))
        self.assertFalse(client.sync_status[0].in_sync)
        self.assertFalse(client.sync_status[0].incremental)
        self.assertTrue(client.sync_status[0].audit)
        self.assertEqual(0, client.sync_status[0].same)
        self.assertEqual(2, client.sync_status[0].created)
        self.assertEqual(0, client.sync_status[0].updated)
        self.assertEqual(0, client.sync_status[0].deleted)
        self.assertEqual(0, client.sync_status[0].to_delete)
        client.sync_status_to_file("audit.csv")


    def test05_run_baseline(self):
        # do a baseline synchronisation on the 2 sources in the mappings
        self.__clear_sources_xml__()

        self.__create_resourcelist__("s1")
        self.__create_resourcelist__("s2")
        self.__clear_destination__()
        mappings = self.__create_mappings__()
        logger.debug("\n=================\n")

        runner = Runner(mappings)
        client = runner.run_baseline()

        self.assertEqual(4, len(client.sync_status))
        # first record is an audit
        self.assertFalse(client.sync_status[0].in_sync)
        self.assertFalse(client.sync_status[0].incremental)
        self.assertTrue(client.sync_status[0].audit)
        self.assertEqual(0, client.sync_status[0].same)
        self.assertEqual(2, client.sync_status[0].created)
        self.assertEqual(0, client.sync_status[0].updated)
        self.assertEqual(0, client.sync_status[0].deleted)
        self.assertEqual(0, client.sync_status[0].to_delete)
        # second record is a create
        self.assertFalse(client.sync_status[1].in_sync)
        self.assertFalse(client.sync_status[1].incremental)
        self.assertFalse(client.sync_status[1].audit)
        self.assertEqual(0, client.sync_status[1].same)
        self.assertEqual(2, client.sync_status[1].created)
        self.assertEqual(0, client.sync_status[1].updated)
        self.assertEqual(0, client.sync_status[1].deleted)
        self.assertEqual(0, client.sync_status[1].to_delete)
        client.sync_status_to_file("baseline.csv")



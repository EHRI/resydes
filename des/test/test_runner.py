#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest, logging, logging.config, os.path, pathlib, glob, shutil, datetime
from des.runner import Runner
from resync.client import Client, ClientFatalError

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

    def __clear_sources_xml__(self, src):
        """
        remove all xml files from a source subfolder
        :param src: either 's1' or 's2'
        :return:
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        s = os.path.join(abs_path, "rs/source", src, "*.xml")
        files = glob.glob(s)
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


    def __create_resourcelist__(self, src, checksum=True):
        """
        Create a resourcelist xml for the source denominated by src.
        :param src: either 's1' or 's2'
        :param checksum: should checksums be added to the xml.
        :return:
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        data = [os.path.join(abs_path, "rs/source", src, "files/resource1.txt"),
                os.path.join(abs_path, "rs/source", src, "files/resource2.txt")]
        paths = ",".join(data)
        #logger.debug("paths is a string '%s'", paths)
        outfile = os.path.join(abs_path, "rs/source", src, "resourcelist.xml")

        # create a resourcelist from the files in test/rs/files
        client = Client(checksum=checksum)

        prefix_path = os.path.join(abs_path, "rs/source", src, "files")
        prefix = pathlib.Path(prefix_path).as_uri()
        resourcedir = os.path.join(abs_path, "rs/source", src, "files")
        args = [prefix, resourcedir]

        client.set_mappings(args)
        client.write_resource_list(paths, outfile)

    def __create_changelist__(self, src, checksum=True):
        """
        Create a changelist xml for the source denominated by src.
        :param src: either 's1' or 's2'
        :param checksum: should checksums be added to the xml.
        :return:
        """
        abs_path = os.path.dirname(os.path.abspath(__name__))
        data = [os.path.join(abs_path, "rs/source", src, "files/resource1.txt"),
                os.path.join(abs_path, "rs/source", src, "files/resource2.txt")]
        paths = ",".join(data)

        outfile = os.path.join(abs_path, "rs/source", src, "changelist.xml")

        ref_sitemap = pathlib.Path(os.path.join(abs_path, "rs/source", src, "resourcelist.xml")).as_uri()

        client = Client(checksum=checksum)

        prefix_path = os.path.join(abs_path, "rs/source", src, "files")
        prefix = pathlib.Path(prefix_path).as_uri()
        resourcedir = os.path.join(abs_path, "rs/source", src, "files")
        args = [prefix, resourcedir]
        client.set_mappings(args)

        client.write_change_list(paths=paths, outfile=outfile, ref_sitemap=ref_sitemap)

    def __change_resource__(self, src, resource):
        abs_path = os.path.dirname(os.path.abspath(__name__))
        filename = os.path.join(abs_path, "rs/source", src, "files", resource + ".txt")
        with open(filename, "a") as file:
            file.write("\n%s" % str(datetime.datetime.now()))


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
        self.__clear_sources_xml__("s1")
        self.__clear_sources_xml__("s2")

        self.__create_resourcelist__("s2")
        self.__clear_destination__()
        runner = Runner(self.__create_mappings__())
        # should continue with syncing the mappings, even if some sources do not expose a resource.xml
        desclient = runner.run_baseline()
        # should report the error
        desclient.sync_status_to_file("logs/baseline-err.csv")

    def test04_run_audit(self):
        # do an audit on the 2 sources in the mappings
        self.__clear_sources_xml__("s1")
        self.__clear_sources_xml__("s2")
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
        client.sync_status_to_file("logs/audit.csv")


    def test05_run_baseline(self):
        # do a baseline synchronisation on the 2 sources in the mappings
        self.__clear_sources_xml__("s1")
        self.__clear_sources_xml__("s2")
        self.__create_resourcelist__("s1", checksum=False)
        self.__create_resourcelist__("s2", checksum=True)
        self.__clear_destination__()
        self.assertFalse(os.path.isdir("rs/destination/d1/files"))
        self.assertFalse(os.path.isdir("rs/destination/d2/files"))

        mappings = self.__create_mappings__()

        # first do a baseline with destination folders empty
        logger.debug("\n=================\n")
        runner = Runner(mappings)
        client_1 = runner.run_baseline()

        # we set checksum=True initially on the client and it should stay like that during the complete run of all
        # the sources.
        self.assertTrue(client_1.checksum)

        client_1.sync_status_to_file("logs/baseline.csv")
        self.assertEqual(4, len(client_1.sync_status))
        # first record is an audit
        self.assertFalse(client_1.sync_status[0].in_sync)
        self.assertFalse(client_1.sync_status[0].incremental)
        self.assertTrue(client_1.sync_status[0].audit)
        self.assertEqual(0, client_1.sync_status[0].same)
        self.assertEqual(2, client_1.sync_status[0].created)
        self.assertEqual(0, client_1.sync_status[0].updated)
        self.assertEqual(0, client_1.sync_status[0].deleted)
        self.assertEqual(0, client_1.sync_status[0].to_delete)
        # second record is a create
        self.assertFalse(client_1.sync_status[1].in_sync)
        self.assertFalse(client_1.sync_status[1].incremental)
        self.assertFalse(client_1.sync_status[1].audit)
        self.assertEqual(0, client_1.sync_status[1].same)
        self.assertEqual(2, client_1.sync_status[1].created)
        self.assertEqual(0, client_1.sync_status[1].updated)
        self.assertEqual(0, client_1.sync_status[1].deleted)
        self.assertEqual(0, client_1.sync_status[1].to_delete)
        client_1.sync_status_to_file("logs/baseline.csv")

        # second do a baseline with destination folders up to date
        logger.debug("\n=================\n")
        client_2 = runner.run_baseline()
        self.assertNotEqual(client_1, client_2)
        self.assertEqual(2, len(client_2.sync_status))
        self.assertTrue(client_2.sync_status[0].in_sync)
        self.assertFalse(client_2.sync_status[0].incremental)
        self.assertTrue(client_2.sync_status[0].audit)
        self.assertEqual(2, client_2.sync_status[0].same)
        self.assertEqual(0, client_2.sync_status[0].created)
        self.assertEqual(0, client_2.sync_status[0].updated)
        self.assertEqual(0, client_2.sync_status[0].deleted)
        self.assertEqual(0, client_2.sync_status[0].to_delete)
        client_2.sync_status_to_file("logs/baseline.csv")

    def test06_read_mappings(self):
        mappings = self.__create_mappings__()
        with open("rs/mappings.txt", "w") as file:
            for item in mappings:
                file.write("%s\n" % item)
            file.close()

        runner = Runner()
        runner.read_mappings("rs/mappings.txt")
        self.assertEqual(mappings, runner.mappings)

    def test21_incremental(self):
        # only one changelist present
        self.__clear_sources_xml__("s1")
        self.__clear_sources_xml__("s2")
        self.__create_resourcelist__("s1", checksum=False)
        self.__create_resourcelist__("s2", checksum=True)
        self.__create_changelist__("s1")
        mappings = self.__create_mappings__()

        logger.debug("\n=================\n")
        runner = Runner(mappings)
        desclient = runner.run_incremental(dryrun=True)
        desclient.sync_status_to_file("logs/incremental_audit.csv")

        self.assertEqual(2, len(desclient.sync_status))

        self.assertTrue(desclient.sync_status[0].in_sync)
        self.assertIsNone(desclient.sync_status[1].in_sync)

        self.assertIsNone(desclient.sync_status[0].exception)
        self.assertIsNotNone(desclient.sync_status[1].exception)

    def test22_incremental(self):
        # one source changed
        self.__clear_sources_xml__("s1")
        self.__clear_sources_xml__("s2")
        self.__create_resourcelist__("s1", checksum=False)
        self.__create_resourcelist__("s2", checksum=True)
        self.__change_resource__("s1", "resource1")
        self.__create_changelist__("s1")
        self.__create_changelist__("s2")
        mappings = self.__create_mappings__()

        logger.debug("\n=================\n")
        runner = Runner(mappings)
        desclient = runner.run_incremental(dryrun=False)
        desclient.sync_status_to_file("logs/incremental.csv")

        # 2 times for the changed source + 1 time for the unchanged one
        self.assertEqual(3, len(desclient.sync_status))
        # s1 not in sync
        self.assertFalse(desclient.sync_status[0].in_sync)
        # s1 is updated
        self.assertEqual(1, desclient.sync_status[1].updated)
        # s2 in sync
        self.assertTrue(desclient.sync_status[2].in_sync)

    def test23_incremental(self):
        # one source changed, is checksum checked?
        self.__clear_sources_xml__("s1")
        self.__clear_sources_xml__("s2")
        self.__create_resourcelist__("s1", checksum=True)
        self.__create_resourcelist__("s2", checksum=True)
        self.__change_resource__("s1", "resource1")
        self.__create_changelist__("s1")
        self.__create_changelist__("s2")
        # mess around with the resource so checksums don't match
        self.__change_resource__("s1", "resource1")
        mappings = self.__create_mappings__()

        # only emits INFO messages in standard log-output. Mismatch of individual resources should be reported.
        logger.debug("\n=================\n")
        runner = Runner(mappings)
        desclient = runner.run_incremental(dryrun=False)
        desclient.sync_status_to_file("logs/incremental.csv")

    def test41_explore(self):
        mappings = self.__create_mappings__()

        logger.debug("\n=================\n")
        runner = Runner(mappings)
        desclient = runner.run_explore()



#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, os, requests, tempfile, shutil, pathlib
import des.reporter
from tempfile import NamedTemporaryFile
from zipfile import ZipFile, BadZipFile
from enum import Enum
from resync.sitemap import Sitemap
from resync.resource_list_builder import ResourceListBuilder
from resync.mapper import Mapper


class Status(Enum):
    """
    The status of the dump process
    """
    init = 1                        # process is in initial state.
    read_error = 2                  # process tried to read its assigned uri but failed.
    downloaded = 3                  # process has downloaded uri contents.
    unzip_error = 4                 # process could not unzip packed content
    unzipped = 5                    # process has unzipped the packed content.
    processed_with_exceptions = 6   # processor has done implied actions according to document from assigned uri
                                    # but did not succeed completely.
    processed = 7                   # processor has done implied actions according to document from assigned uri.


class Redump(object):

    def __init__(self, pack_uri):
        """
        Initialize a Redump.
        :param pack_uri: the uri of packed content. (For the moment only zip-files will be accepted.)
        :return:
        """
        self.logger = logging.getLogger(__name__)
        self.pack_uri = pack_uri
        self.source_status = None
        self.status = Status.init
        self.exceptions = []

    def process_dump(self):
        self.logger.debug("Start %s on %s" % (self.__class__.__name__, self.pack_uri))
        zipfile = None
        unzipdir = None
        try:
            zipfile = NamedTemporaryFile(delete=False, prefix="resydes_", suffix=".zip")
            self.logger.debug("%s to temp file %s" % (self.pack_uri, zipfile.name))
            self.download_dump(zipfile)
            assert self.status == Status.downloaded, "Incomplete download"

            unzipdir = tempfile.mkdtemp(prefix="resydes_")
            with ZipFile(zipfile.name, "r") as z:
                z.extractall(path=unzipdir)
            self.logger.debug("Unzipped '%s' to '%s'" % (zipfile.name, unzipdir))
            self.status = Status.unzipped

            # desclient = des.desclient.instance()
            # destination = "/private/var/folders/4r/07w38gh12d395r8s9n0pw30w0000gn/T/TemporaryItems"
            # zip_uri = pathlib.Path(os.path.join(unzipdir, "manifest.xml")).as_uri()
            # desclient.set_mappings((zip_uri, destination))
            # desclient.baseline_or_audit(True, False)

            self.synchronize(unzipdir)

        except AssertionError as err:
            self.logger.warn("%s AssertionError: %s" % (self.pack_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.pack_uri, exception=err)

        except BadZipFile as err:
            self.logger.warn("%s BadZipFile: %s" % (self.pack_uri, str(err)))
            self.status = Status.unzip_error
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.pack_uri, exception=err)

        finally:
            if zipfile is not None:
                os.unlink(zipfile.name)
                self.logger.debug("Removed temp file %s" % zipfile.name)

            if unzipdir is not None:
                shutil.rmtree(unzipdir, ignore_errors=True)
                self.logger.debug("Removed temp dir  %s" % unzipdir)

    def download_dump(self, file):
        session = requests.Session()
        try:
            with file:
                response = session.get(self.pack_uri)
                self.source_status = response.status_code
                assert self.source_status == 200, "Invalid response status: %d on %s" % (self.source_status, self.pack_uri)

                for block in response.iter_content(1024):
                    file.write(block)

            self.status = Status.downloaded

        except requests.exceptions.ConnectionError as err:
            self.logger.warn("%s No connection: %s" % (self.pack_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.pack_uri, exception=err)

        except AssertionError as err:
            self.logger.warn("%s Error: %s" % (self.pack_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.pack_uri, exception=err)

        finally:
            session.close()

    def synchronize(self, unzipdir):
        manifest_file = os.path.join(unzipdir, "manifest.xml")
        sitemap = Sitemap()
        manifest_doc = sitemap.parse_xml(fh=manifest_file)

        print(manifest_doc)

        destination = "/Users/ecco/tmp/rs"
        mapper=Mapper(("http://localhost:8000/rs/source", destination))
        rlb = ResourceListBuilder(mapper=mapper)
        dst_resource_list = rlb.from_disk()
        print("======================")
        print(dst_resource_list)
        (same, updated, deleted, created) = dst_resource_list.compare(manifest_doc)
        print(len(same), len(updated), len(deleted), len(created))

        print("same")
        for resource in same:
            print(resource)
        print("updated")
        for resource in updated:
            print(resource)
        print("deleted")
        for resource in deleted:
            print(resource)
        print("created")
        for resource in created:
            print(resource)


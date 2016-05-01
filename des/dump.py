#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, os, requests, tempfile, shutil, pathlib
import des.reporter
from des.config import Config
from des.location_mapper import DestinationMap
from tempfile import NamedTemporaryFile
from zipfile import ZipFile, BadZipFile
from enum import Enum
from resync.sitemap import Sitemap, SitemapParseError
from resync.resource_list_builder import ResourceListBuilder
from resync.mapper import Mapper


CAPA_RESOURCEDUMP_MANIFEST = "resourcedump-manifest"
CAPA_CHANGEDUMP_MANIFEST = "changedump-manifest"


class Status(Enum):
    """
    The status of the dump process.
    """
    init = 1                        # process is in initial state.
    download_error = 2              # process tried to download the packed content but failed.
    downloaded = 3                  # process has downloaded packed content.
    unzip_error = 4                 # process could not unzip packed content
    unzipped = 5                    # process has unzipped the packed content.
    parse_error = 6                 # sitemap (manifest.xml) could not be parsed
    parsed = 7                      # sitemap (manifest.xml) is parsed
    processed_with_exceptions = 8   # processed implied actions according to manifest document
                                    # but did not succeed completely.
    processed = 9                   # processed implied actions according to manifest document.


# Collection of dump listeners.
# Added dump listeners (up till now a dump listener is duck-type-same as processor.ProcessorListener) will be informed
# of following events:
#   - event_sitemap_received(uri, capability, text)
#       uri = pack_uri, capability = "resourcedump-manifest" | "changedump-manifest", text = sitemap = manifest.xml
dump_listeners = []


class Redump(object):
    """
    A resource dump and a change dump will have similarities in processing - up to Status.parsed.
    This parent object is meant to do the common processing of resource dump and change dump.
    """

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
        """
        Do all the processsing needed to effectuate a resource dump or a change dump.
        :return:
        """
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

            self.base_line(unzipdir)

        except AssertionError as err:
            self.logger.warn("%s AssertionError: %s" % (self.pack_uri, str(err)))
            self.status = Status.download_error
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
        """
        Download the contents of the pack-uri.
        :param file: the file to write to
        :return:
        """
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
            self.status = Status.download_error
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.pack_uri, exception=err)

        except AssertionError as err:
            self.logger.warn("%s Error: %s" % (self.pack_uri, str(err)))
            self.status = Status.download_error
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.pack_uri, exception=err)

        finally:
            session.close()

    def base_line(self, unzipdir):
        """
        Synchronize the unzipped contents of a resource dump with the local resources
        :param unzipdir: the directory of the unzipped packed contents.
        :return:
        """
        manifest_file_name = os.path.join(unzipdir, "manifest.xml")
        try:
            sitemap = Sitemap()
            manifest_doc = sitemap.parse_xml(fh=manifest_file_name)
            # the manifest_doc is a resync.resource_container.ResourceContainer
            capability = manifest_doc.capability
            assert capability == CAPA_RESOURCEDUMP_MANIFEST, "Capability is not %s but %s" % (CAPA_RESOURCEDUMP_MANIFEST, capability)
            self.status = Status.parsed
            self.__inform_sitemap_received__(capability, manifest_file_name)

            config = Config()
            netloc = config.boolean_prop(Config.key_use_netloc, False)
            base_uri, destination = DestinationMap().find_destination(self.pack_uri, netloc=netloc)
            assert destination is not None, "Found no destination folder in DestinationMap"
            mapper=Mapper((base_uri, destination))
            rlb = ResourceListBuilder(mapper=mapper)
            dst_resource_list = rlb.from_disk()
            # Compares on uri
            same, updated, deleted, created = dst_resource_list.compare(manifest_doc)

            raise NotImplementedError("This class is not fully implemented.")

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
                base_uri, local_path = DestinationMap().find_local_path(resource.uri)
                print(base_uri, local_path)

        except AssertionError as err:
            self.logger.debug("%s Error: %s" % (self.pack_uri, str(err)))
            self.status = Status.parse_error
            self.exceptions.append(err)
        except SitemapParseError as err:
            self.logger.debug("%s Unreadable source: %s" % (self.source_uri, str(err)))
            self.status = Status.parse_error
            self.exceptions.append(err)

        self.status = Status.processed_with_exceptions if self.has_exceptions() else Status.processed

    def has_exceptions(self):
        """
        Check whether the processing of packed content ran into exceptions.
        :return: True if this Redump ran into exceptions, False otherwise.
        """
        return len(self.exceptions) != 0

    def __inform_sitemap_received__(self, capability, manifest_file_name):
        if len(dump_listeners) > 0:
            uri = os.path.join(self.pack_uri, "manifest.xml")
            with open(manifest_file_name) as file:
                text = file.read()
            for listener in dump_listeners:
                listener.event_sitemap_received(uri, capability, text)




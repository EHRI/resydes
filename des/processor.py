#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import abc
import logging
import urllib.parse
import xml
import xml.etree.ElementTree as ET

import requests

import des.desclient
import des.reporter
import resync
import resync.w3c_datetime as w3c
from des.status import Status
from des.sync import Relisync, Chanlisync
from des.dump import Redump
from resync.sitemap import Sitemap
from resync.client_state import ClientState

WELLKNOWN_RESOURCE = ".well-known/resourcesync"

SITEMAP_ROOT = "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"
SITEMAP_INDEX_ROOT = "{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex"

CAPA_DESCRIPTION = "description"
CAPA_CAPABILITYLIST = "capabilitylist"
CAPA_RESOURCELIST = "resourcelist"
CAPA_RESOURCEDUMP = "resourcedump"
CAPA_CHANGELIST = "changelist"
CAPA_CHANGEDUMP = "changedump"


class ProcessorListener(object):

    def event_text_recieved(self, uri, text):
        pass

processor_listeners = []


class Processor(object):
    """
    Reads a sitemap from a uri and turns it into a resync.resource_container.ResourceContainer
    """

    def __init__(self, source_uri, expected_capability, report_errors=True):
        """
        Initialize this class.
        :param source_uri: the uri of the sitemap that must be read
        :param expected_capability: the expected capability of the sitemap
        :return: None
        """
        self.logger = logging.getLogger(__name__)
        self.status = Status.init
        self.source_uri = source_uri
        self.capability = expected_capability
        self.report_errors = report_errors

        self.source_status = None
        self.exceptions = []
        self.source_document = None
        self.describedby_url = None
        self.up_url = None
        self.is_index = False

    def read_source(self):
        """
        Read the source_uri and parse it to source_document.
        :return: True if the document was downloaded and parsed without exceptions, False otherwise.
        """
        session = requests.Session()
        try:
            response = session.get(self.source_uri)
            self.source_status = response.status_code
            self.logger.debug("Read %s, status %s" % (self.source_uri, str(self.source_status)))
            assert self.source_status == 200, "Invalid response status: %d" % self.source_status

            text = response.text

            root = ET.fromstring(text)
            self.is_index = root.tag == SITEMAP_INDEX_ROOT

            etree = ET.ElementTree(root)
            sitemap = Sitemap()
            self.source_document = sitemap.parse_xml(etree=etree)
            # the source_document is a resync.resource_container.ResourceContainer
            capability = self.source_document.capability
            assert capability == self.capability, \
                "Capability is not %s but %s" % (self.capability, capability)
            # anyone interested in text?
            for processor_listener in processor_listeners:
                processor_listener.event_text_recieved(self.source_uri, text)

            self.describedby_url = self.source_document.describedby
            self.up_url = self.source_document.up # to a parent non-index document
            self.index_url = self.source_document.index # to a parent index document
            self.status = Status.document

        except requests.exceptions.ConnectionError as err:
            self.logger.debug("%s No connection: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.__report__(err)

        except xml.etree.ElementTree.ParseError as err:
            self.logger.debug("%s ParseError: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.__report__(err)

        except resync.sitemap.SitemapParseError as err:
            self.logger.debug("%s Unreadable source: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.__report__(err)

        except AssertionError as err:
            self.logger.debug("%s Error: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.__report__(err)

        finally:
            session.close()

        return self.status == Status.document

    def __report__(self, err):
        if self.report_errors:
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.source_uri, exception=err)

    def has_exceptions(self):
        return len(self.exceptions) != 0

    @abc.abstractmethod
    def process_source(self):
        """
        Check that the source document is loaded and correct and if so do any processing the source document implies.
        :return: None
        """
        raise NotImplementedError

    def __assert_document__(self):
        """
        Make sure the source document is loaded and correct.
        :return: True if source document is loaded and correct, False otherwise
        """
        self.logger.debug("Start %s on %s" % (self.__class__.__name__, self.source_uri))
        if not self.status is Status.document:
            self.read_source()
        if not self.status is Status.document:
            self.logger.debug("Not processing %s because of previous errors" % self.source_uri)
        return self.status == Status.document


class RelayProcessor(Processor):
    """
    Documents in the Resource Sync Framework can be sitemapindexes, pointing recursively to documents of the same type,
    or urlsets, pointing to documents or resources lower in the framework hierarchy.
    (See also: http://www.openarchives.org/rs/1.0/resourcesync#fig_framework_structure)
    RelayProcessor hands over the processing to the next processor based on the source_document being an index or not.

    """

    @abc.abstractmethod
    def __process_lower__(self):
        """
        Process the document if it is a urlset.
        :return: None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __get_level_processor__(self, uri):
        """
        Get the processor capable of handling documents of the same capability.
        :param uri: The uri of the document the level processor will process.
        :return: Initialized processor
        """
        raise NotImplementedError

    def __process_index__(self):
        """
        Process the document if it is a sitemapindex.
        :return: None
        """
        for resource in self.source_document.resources:
            capability = resource.capability
            if capability == self.capability: # a index can only point to sitemaps or urlsets with the same capability.
                processor = self.__get_level_processor__(resource.uri)
                processor.process_source()
                self.exceptions.extend(processor.exceptions)
            else:
                self.logger.debug("Unexpected capability %s in %s" % (capability, self.source_uri))
                self.exceptions.append("Unexpected capability %s in %s" % (capability, self.source_uri))

    def process_source(self):
        if not self.__assert_document__():
            return
        # the source document is a urlset (non-index) or a sitemapindex.
        if self.is_index:
            self.__process_index__()
        else:
            self.__process_lower__()
        self.status = Status.processed_with_exceptions if self.has_exceptions() else Status.processed


class Sodesproc(RelayProcessor):
    """
    SourceDescription eats the base uri of a source, looks for a .well-known/resourcesync and processes the contents.
    """
    def __init__(self, base_uri, report_errors=True):
        # urllib.parse.urljoin leaves out the last part of a path if it doesn't end with '/'
        if base_uri.endswith("/"):
            self.base_uri = base_uri
        else:
            self.base_uri = base_uri + "/"
        wellknown = urllib.parse.urljoin(self.base_uri, WELLKNOWN_RESOURCE)
        super(Sodesproc, self).__init__(wellknown, CAPA_DESCRIPTION, report_errors=report_errors)

    def __get_level_processor__(self, uri):
        return Sodesproc(uri)

    def __process_lower__(self):
        # the source document is a source description
        for resource in self.source_document.resources:
            # it contains links to capabilitylists
            capaproc = Capaproc(resource.uri)
            capaproc.process_source()
            self.exceptions.extend(capaproc.exceptions)


class Capaproc(Processor):
    """
    Capaproc eats the uri of a capability list and processes the contents.
    """
    def __init__(self, uri, report_errors=True):
        super(Capaproc, self).__init__(uri, CAPA_CAPABILITYLIST, report_errors=report_errors)

    def process_source(self):
        if not self.__assert_document__():
            return

        # the source document is a capability list or a capability index
        for resource in self.source_document.resources:
            capability = resource.capability
            processor = None
            if capability == CAPA_CAPABILITYLIST:
                # recursive: a capability index points to other capability lists
                processor = Capaproc(resource.uri)
            elif capability == CAPA_RESOURCELIST:
                processor = Reliproc(resource.uri)
            elif capability == CAPA_RESOURCEDUMP:
                processor = Redumpproc(resource.uri)
            elif capability == CAPA_CHANGELIST:
                processor = Chanliproc(resource.uri)
            elif capability == CAPA_CHANGEDUMP:
                pass
            else:
                self.logger.debug("Unknown capability %s in %s" % (capability, self.source_uri))
                self.exceptions.append("Unknown capability %s in %s" % (capability, self.source_uri))

            if processor is not None:
                processor.process_source()
                self.exceptions.extend(processor.exceptions)

        self.status = Status.processed_with_exceptions if self.has_exceptions() else Status.processed


class Reliproc(RelayProcessor):
    """
    Reliproc eats the uri of a resource list and processes the contents.

    """
    def __init__(self, uri):
        super(Reliproc, self).__init__(uri, CAPA_RESOURCELIST)

    def __get_level_processor__(self, uri):
        return Reliproc(uri)

    def __process_lower__(self):
        processor = Relisync(self.source_uri)
        processor.process_source()
        self.exceptions.extend(processor.exceptions)


class Chanliproc(RelayProcessor):
    """
    Chanliproc eats the uri of a change list and processes the contents.
    """
    def __init__(self, uri):
        super(Chanliproc, self).__init__(uri, CAPA_CHANGELIST)

    def __get_level_processor__(self, uri):
        return Chanliproc(uri)

    def __process_lower__(self):
        processor = Chanlisync(self.source_uri)
        processor.process_source()
        self.exceptions.extend(processor.exceptions)


class Redumpproc(RelayProcessor):
    """
    Redumpproc eats the uri of a resource dump and processes the contents.
    """
    def __init__(self, uri):
        super(Redumpproc, self).__init__(uri, CAPA_RESOURCEDUMP)

    def __get_level_processor__(self, uri):
        return Redumpproc(uri)

    def __process_lower__(self):
        # the source document is a urlset with url/loc's pointing to packaged resources.
        md_at = w3c.str_to_datetime(self.source_document.md_at) # 'must have' at attribute
        last_synced = ClientState().get_state(self.source_uri)
        if last_synced is None or md_at > last_synced:
            for resource in self.source_document.resources:
                self.__process_resource__(resource)

            if len(self.exceptions) == 0:
                ClientState().set_state(self.source_uri, md_at)
        else:
            self.logger.debug("In sync: %s" % self.source_uri)
            des.reporter.instance().log_status(uri=self.source_uri, in_sync=True)

    def __process_resource__(self, resource):
        # the resource points to a resource dump.
        md_at = w3c.str_to_datetime(resource.md_at) # 'may have' at attribute
        last_synced = ClientState().get_state(resource.uri)
        if last_synced is None or md_at is None or md_at > last_synced:
            self.__process_dump__(resource.uri)
        else:
            des.reporter.instance().log_status(uri=resource.uri, in_sync=True)

    def __process_dump__(self, uri):
        redump = Redump(uri)
        redump.process_dump()
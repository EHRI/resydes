#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests, urllib.parse, xml, abc
import xml.etree.ElementTree as ET
import resync
from enum import Enum
from resync.sitemap import Sitemap
from des.location_mapper import DestinationMap

WELLKNOWN_RESOURCE = ".well-known/resourcesync"
CAPA_DESCRIPTION = "description"
CAPA_CAPABILITYLIST = "capabilitylist"
CAPA_RESOURCELIST = "resourcelist"
CAPA_RESOURCEDUMP = "resourcedump"
CAPA_CHANGELIST = "changelist"
CAPA_CHANGEDUMP = "changedump"


class Status(Enum):
    init = 1
    read_error = 2
    document = 3
    processed_with_exceptions = 4
    processed = 5

class Processor(object):
    """
    Reads a sitemap from a uri and turns it into a resync.resource_container.ResourceContainer
    """

    def __init__(self, source_uri, expected_capability):
        """

        :param source_uri: the uri of the sitemap that must be read
        :param expected_capability: the expected capability of the sitemap
        :return: None
        """
        self.logger = logging.getLogger(__name__)
        self.status = Status.init
        self.source_uri = source_uri
        self.capability = expected_capability

        self.source_status = None
        self.exceptions = []
        self.source_document = None
        self.describedby_url = None
        self.up_url = None

    def read_source(self):
        """

        :return:
        """
        session = requests.Session()
        try:
            response = session.get(self.source_uri)
            self.source_status = response.status_code
            self.logger.debug("Read %s, status %s" % (self.source_uri, str(self.source_status)))
            assert self.source_status == 200, "Invalid response status: %d" % self.source_status

            text = response.text
            root = ET.fromstring(text)
            sitemap = Sitemap()
            self.source_document = sitemap.parse_xml(etree=ET.ElementTree(root))
            # the source_document is a resync.resource_container.ResourceContainer
            capability = self.source_document.capability
            assert capability == self.capability, \
                "Capability is not %s but %s" % (self.capability, capability)
            self.describedby_url = self.source_document.describedby
            self.up_url = self.source_document.up
            self.status = Status.document

        except requests.exceptions.ConnectionError as err:
            self.logger.debug("%s No connection: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)

        except xml.etree.ElementTree.ParseError as err:
            self.logger.debug("%s ParseError: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)

        except resync.sitemap.SitemapParseError as err:
            self.logger.debug("%s Unreadable source: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)

        except AssertionError as err:
            self.logger.debug("%s Error: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)

        finally:
            session.close()

        return self.status == Status.document

    def has_exceptions(self):
        return len(self.exceptions) != 0

    @abc.abstractmethod
    def process_source(self):
        """

        :return:
        """
        raise NotImplementedError

    def __assert_document__(self):
        """
        Make sure the source document is read and correct.
        :return: True if source document is read and correct, False otherwise
        """
        self.logger.debug("Start %s on %s" % (self.__class__.__name__, self.source_uri))
        if not self.status is Status.document:
            self.read_source()
        if not self.status is Status.document:
            self.logger.debug("Not processing %s because of previous errors" % self.source_uri)
        return self.status == Status.document


class Discoverer(Processor):

    def __init__(self, base_uri):
        self.logger = logging.getLogger(__name__)
        # urllib.parse.urljoin leaves out the last part of a path if it doesn't end with '/'
        if base_uri.endswith("/"):
            self.base_uri = base_uri
        else:
            self.base_uri = base_uri + "/"
        wellknown = urllib.parse.urljoin(self.base_uri, WELLKNOWN_RESOURCE)
        super(Discoverer, self).__init__(wellknown, CAPA_DESCRIPTION)

    def process_source(self):
        if not self.__assert_document__():
            return

        # the source document is a source description
        for resource in self.source_document.resources:
            # it contains links to capabilitylists
            capaproc = Capaproc(resource.uri)
            capaproc.process_source()
            self.exceptions.extend(capaproc.exceptions)

        self.status = Status.processed_with_exceptions if self.has_exceptions() else Status.processed


class Capaproc(Processor):

    def __init__(self, uri):
        self.logger = logging.getLogger(__name__)
        super(Capaproc, self).__init__(uri, CAPA_CAPABILITYLIST)

    def process_source(self):
        if not self.__assert_document__():
            return

        # the source document is a capability list
        for resource in self.source_document.resources:
            capability = resource.capability
            if capability == CAPA_RESOURCELIST:
                relisync = Relisync(resource)
                relisync.process_source()
                self.exceptions.extend(relisync.exceptions)
            elif capability == CAPA_RESOURCEDUMP:
                pass
            elif capability == CAPA_CHANGELIST:
                pass
            elif capability == CAPA_CHANGEDUMP:
                pass
            else:
                self.logger.debug("Unknown capability %s in %s" % (capability, self.source_uri))
                self.exceptions.append("Unknown capability %s in %s" % (capability, self.source_uri))

        self.status = Status.processed_with_exceptions if self.has_exceptions() else Status.processed


class Relisync(object):
    """
    Synchronisation with a resource list. Synchronisation is eventually done with the resync.client.Client
    """
    def __init__(self, resource):
        self.logger = logging.getLogger(__name__)
        self.resource = resource

        self.exceptions = []

    def process_source(self):
        uri = self.resource.uri
        destination = DestinationMap().find_destination(uri, netloc=True)





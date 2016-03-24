#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests, urllib.parse, xml, abc, os.path
import xml.etree.ElementTree as ET
import resync
import des.desclient, des.reporter
from enum import Enum
from resync.sitemap import Sitemap
from resync.client import ClientFatalError
from resync.client_state import ClientState
from des.location_mapper import DestinationMap
from des.config import Config

WELLKNOWN_RESOURCE = ".well-known/resourcesync"

SITEMAP_ROOT = "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"
SITEMAP_INDEX_ROOT = "{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex"

CAPA_DESCRIPTION = "description"
CAPA_CAPABILITYLIST = "capabilitylist"
CAPA_RESOURCELIST = "resourcelist"
CAPA_RESOURCEDUMP = "resourcedump"
CAPA_CHANGELIST = "changelist"
CAPA_CHANGEDUMP = "changedump"


class Status(Enum):
    """
    The status of a Processor
    """
    init = 1                        # processor is in initial state.
    read_error = 2                  # processor tried to read its assigned uri but failed.
    document = 3                    # processor has read and parsed its assigned uri.
    processed_with_exceptions = 4   # processor has done implied actions according to document from assigned uri
                                    # but did not succeed completely.
    processed = 5                   # processor has done implied actions according to document from assigned uri.


class Processor(object):
    """
    Reads a sitemap from a uri and turns it into a resync.resource_container.ResourceContainer
    """

    def __init__(self, source_uri, expected_capability):
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

        self.source_status = None
        self.exceptions = []
        self.source_document = None
        self.describedby_url = None
        self.up_url = None
        self.is_index = False

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
            self.is_index = root.tag == SITEMAP_INDEX_ROOT

            etree = ET.ElementTree(root)
            sitemap = Sitemap()
            self.source_document = sitemap.parse_xml(etree=etree)
            # the source_document is a resync.resource_container.ResourceContainer
            capability = self.source_document.capability
            assert capability == self.capability, \
                "Capability is not %s but %s" % (self.capability, capability)
            self.describedby_url = self.source_document.describedby
            self.up_url = self.source_document.up # to a parent non-index document
            self.index_url = self.source_document.index # to a parent index document
            self.status = Status.document

        except requests.exceptions.ConnectionError as err:
            self.logger.debug("%s No connection: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.source_uri, exception=err)

        except xml.etree.ElementTree.ParseError as err:
            self.logger.debug("%s ParseError: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.source_uri, exception=err)

        except resync.sitemap.SitemapParseError as err:
            self.logger.debug("%s Unreadable source: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.source_uri, exception=err)

        except AssertionError as err:
            self.logger.debug("%s Error: %s" % (self.source_uri, str(err)))
            self.status = Status.read_error
            self.exceptions.append(err)
            des.reporter.instance().log_status(self.source_uri, exception=err)

        finally:
            session.close()

        return self.status == Status.document

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


class Wellknown(Processor):
    """
    Wellknown eats the base uri of a source, looks for a .well-known/resourcesync and processes the contents.
    """
    def __init__(self, base_uri):
        self.logger = logging.getLogger(__name__)
        # urllib.parse.urljoin leaves out the last part of a path if it doesn't end with '/'
        if base_uri.endswith("/"):
            self.base_uri = base_uri
        else:
            self.base_uri = base_uri + "/"
        wellknown = urllib.parse.urljoin(self.base_uri, WELLKNOWN_RESOURCE)
        super(Wellknown, self).__init__(wellknown, CAPA_DESCRIPTION)

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
    """
    Capaproc eats the uri of a capability list and processes the contents.
    """
    def __init__(self, uri):
        self.logger = logging.getLogger(__name__)
        super(Capaproc, self).__init__(uri, CAPA_CAPABILITYLIST)

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
                pass
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


class Reliproc(Processor):
    """
    Reliproc eats the uri of a resource list and processes the contents.

    """
    def __init__(self, uri):
        self.logger = logging.getLogger(__name__)
        super(Reliproc, self).__init__(uri, CAPA_RESOURCELIST)

    def process_source(self):
        if not self.__assert_document__():
            return

        # the source document is a resource list or a resource index
        if self.is_index:
            for resource in self.source_document.resources:
                capability = resource.capability
                if capability == CAPA_RESOURCELIST:
                    # recursive: a resource index points to other resource lists
                    processor = Reliproc(resource.uri)
                    processor.process_source()
                    self.exceptions.extend(processor.exceptions)
                else:
                    self.logger.debug("Unexpected capability %s in %s" % (capability, self.source_uri))
                    self.exceptions.append("Unexpected capability %s in %s" % (capability, self.source_uri))
        else:
            processor = Relisync(self.source_uri)
            processor.process_source()
            self.exceptions.extend(processor.exceptions)


class Chanliproc(Processor):
    """
    Chanliproc eats the uri of a change list and processes the contents.
    """
    def __init__(self, uri):
        self.logger = logging.getLogger(__name__)
        super(Chanliproc, self).__init__(uri, CAPA_CHANGELIST)

    def process_source(self):
        if not self.__assert_document__():
            return

        # the source document is a change list or a change index
        if self.is_index:
            for resource in self.source_document.resources:
                capability = resource.capability
                if capability == CAPA_CHANGELIST:
                    # recursive: a change index points to other change lists
                    processor = Chanliproc(resource.uri)
                    processor.process_source()
                    self.exceptions.extend(processor.exceptions)
                else:
                    self.logger.debug("Unexpected capability %s in %s" % (capability, self.source_uri))
                    self.exceptions.append("Unexpected capability %s in %s" % (capability, self.source_uri))
        else:
            processor = Chanlisync(self.source_uri)
            processor.process_source()
            self.exceptions.extend(processor.exceptions)


class Resync(object):
    """
    Synchronisation with the resync.client.Client
    """
    def __init__(self, uri):
        """
        Initialize a Resync
        :param uri: The uri pointing to a resource list If the uri ends with something other than
        'resourcelist.xml' you're in trouble.
        :return: None
        """
        self.logger = logging.getLogger(__name__)
        self.uri = uri

        self.exceptions = []
        self.status = Status.init

    @abc.abstractmethod
    def do_synchronize(self, desclient, allow_deletion, audit_only):
        raise NotImplementedError

    def has_exceptions(self):
        return len(self.exceptions) != 0

    def process_source(self):
        config = Config()
        netloc = config.boolean_prop(Config.key_use_netloc, False)
        destination = DestinationMap().find_destination(self.uri, netloc=netloc)
        if destination is None:
            self.logger.debug("No destination for %s" % self.uri)
            self.exceptions.append("No destination for %s" % self.uri)
            des.reporter.instance().log_status(self.uri,
                exception="No destination specified and use of net location prohibited.")
        else:
            self.__synchronize__(destination)

        self.status = Status.processed_with_exceptions if self.has_exceptions() else Status.processed

    def __synchronize__(self, destination):
        config = Config()
        checksum = config.boolean_prop(Config.key_use_checksum, True)
        audit_only = config.boolean_prop(Config.key_audit_only, True)
        allow_deletion = not audit_only

        desclient = des.desclient.instance()
        # we have to strip 'resourcelist.xml' etc. from the uri because of workings of resync.
        #uri = os.path.dirname(self.uri)
        #self.logger.debug("Converted '%s' to '%s'" % (self.uri, uri))
        try:
            desclient.set_mappings((self.uri, destination))
            self.do_synchronize(desclient, allow_deletion, audit_only)
        except ClientFatalError as err:
            self.logger.warn("EXCEPTION while syncing %s" % self.uri, exc_info=True)
            desclient.log_status(exception=err)
            self.exceptions.append(err)
        finally:
            # A side effect (or a bug ;) is messing around with the
            # class-level property Client.checksum. Make sure it is always set to initial value before the next
            # source is processed.
            desclient.checksum = checksum


class Relisync(Resync):
    """
    Synchronisation of a resource list. Synchronisation is eventually done with the resync.client.Client

    """
    def __init__(self, uri):
        """
        Initialize a Relisync
        :param uri: The uri pointing to a resource list If the uri ends with something other than
        'resourcelist.xml' you're in trouble.
        :return: None
        """
        super(Relisync, self).__init__(uri)

    def do_synchronize(self, desclient, allow_deletion, audit_only):
        desclient.baseline_or_audit(allow_deletion, audit_only)


class Chanlisync(Resync):
    """
    Synchronisation of a change list. Synchronisation is eventually done with the resync.client.Client

    """
    def __init__(self, uri):
        """
        Initialize a Chanlisync
        :param uri: The uri pointing to a change list If the uri ends with something other than
        'changelist.xml' you're in trouble.
        :return: None
        """
        super(Chanlisync, self).__init__(uri)

    def do_synchronize(self, desclient, allow_deletion, audit_only):
        #
        # State is now kept for the full url of resourcelist and changelist (whatever there names may be).
        # The first time we go from baseline to incremental there will be no state for that particular url.
        #
        from_datetime = ClientState().get_state(self.uri)
        if from_datetime is None:
            from_datetime = "1999"
        else:
            from_datetime = None # only set this parameter when no state is present

        desclient.incremental(allow_deletion=allow_deletion, from_datetime=from_datetime)
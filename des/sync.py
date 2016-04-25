#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import abc
import logging

import des.desclient
import des.reporter

from des.config import Config
from des.location_mapper import DestinationMap
from des.status import Status
from resync.client import ClientFatalError
from resync.client_state import ClientState


class Resync(object):
    """
    Synchronisation with the resync.client.Client
    """
    def __init__(self, uri):
        """
        Initialize a Resync
        :param uri: The uri pointing to a resource list or change list.
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
        base_uri, destination = DestinationMap().find_destination(self.uri, netloc=netloc)
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
        :param uri: The uri pointing to a resource list.
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
        :param uri: The uri pointing to a change list.
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
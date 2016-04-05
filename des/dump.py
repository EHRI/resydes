#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, os, requests
import des.reporter
from tempfile import NamedTemporaryFile
from zipfile import ZipFile
from des.status import Status


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
        f = None
        try:
            f = NamedTemporaryFile(delete=False, prefix="resydes", suffix=".zip")
            self.logger.debug("%s to temp file %s" % (self.pack_uri, f.name))
            self.download_dump(f)
            # self.unzip_dump(f) @ToDo unzip in tmp-directory

        finally:
            if f is not None:
                os.unlink(f.name)
                self.logger.debug("Removed temp file %s" % f.name)

    def download_dump(self, f):
        session = requests.Session()
        try:
            with f:
                response = session.get(self.pack_uri)
                self.source_status = response.status_code
                assert self.source_status == 200, "Invalid response status: %d" % self.source_status

                for block in response.iter_content(1024):
                    f.write(block)

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

    def unzip_dump(self, f):
        with ZipFile(f.name, "r") as z:
                z.extractall()

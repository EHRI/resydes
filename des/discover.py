#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, requests, des.reporter, urllib
from html.parser import HTMLParser
from des.status import Status
from des.processor import Sodesproc, Capaproc, Reliproc


class Discoverer(object):

    def __init__(self, uri):
        """

        :param uri:
        :return:
        """
        self.logger = logging.getLogger(__name__)
        self.uri = uri

    def get_processor(self):
        """
        Discover the resource sync method for the uri.
        :return: a processor for the uri or None if we cannot find one
        """
        processor = self.try_wellknown()
        if processor is None:
            processor = self.try_capabilitylist()
        if processor is None:
            processor = self.try_link_html()
        if processor is None:
            processor = self.try_link_http()
        if processor is None:
            processor = self.try_robots()
        if processor is None:
            msg = "Could not discover resource sync method for %s" % self.uri
            self.logger.warn(msg)
        return processor

    def try_wellknown(self):
        """
        The uri can be extended with '.well-known/resourcesync' which leads to a valid source description.
        :return: SourceDescriptionproc on a source description or None
        """
        processor = Sodesproc(self.uri, report_errors=False)
        processor.read_source()
        if processor.status == Status.document:
            processor.report_errors = True
            return processor
        else:
            return None

    def try_capabilitylist(self):
        """
        The uri leads to a valid capabilitylist.
        :return: a Capaproc on a capabilitylist or None
        """
        processor = Capaproc(self.uri, report_errors=False)
        processor.read_source()
        if processor.status == Status.document:
            processor.report_errors = True
            return processor
        else:
            return None

    def try_link_html(self):
        """
        <html>
            <head>
                <link rel="resourcesync" href="http://www.example.com/dataset1/capabilitylist.xml"/>
        :return: a Capaproc on a capabilitylist or None
        """
        processor = None
        session = requests.Session()
        try:
            response = session.get(self.uri)
            self.logger.debug("Read %s, status %s" % (self.uri, str(response.status_code)))
            assert response.status_code == 200, "Invalid response status: %d" % response.status_code
            text = response.text
            parser = RSyncParser()
            parser.feed(text)
            parser.close()
            link = parser.link
            if link is not None:
                # @ToDo find out if it is a relative link
                # A Capability List may be made discoverable by means of links provided ... in an HTML document
                processor = Capaproc(link)

        except requests.exceptions.ConnectionError as err:
            self.logger.debug("%s No connection: %s" % (self.uri, str(err)))

        except AssertionError as err:
            self.logger.debug("%s Error: %s" % (self.uri, str(err)))

        finally:
            session.close()

        return processor


    def try_link_http(self):
        """
        Link: <http://www.example.com/dataset1/capabilitylist.xml>; rel="resourcesync"
        :return: a Capaproc on a capabilitylist or None
        """
        processor = None

        self.logger.warn("Discover Resource Sync in http header not implemented")

        return processor

    def try_robots(self):
        """
        Sitemap: http://example.com/dataset1/resourcelist.xml
        :return:
        """
        processor = None
        if self.uri.endswith("/"):
            uri = urllib.parse.urljoin(self.uri, "robots.txt")
        else:
            uri = urllib.parse.urljoin(self.uri + "/", "robots.txt")

        session = requests.Session()
        try:
            response = session.get(uri)
            self.logger.debug("Read %s, status %s" % (uri, str(response.status_code)))
            assert response.status_code == 200, "Invalid response status: %d" % response.status_code
            text = response.text
            links = []
            for line in text.splitlines():
                if line.strip() == "":
                    pass
                else:
                    k, v = line.split(":", 1)
                    if k.strip() == "Sitemap":
                        links.append(v.strip())

            # @ToDo multiple sitemaps may be mentioned.
            # For now take the first
            if len(links) > 0:
                processor = Reliproc(links[0])
            if len(links) > 1:
                self.logger.warn("Discover more than one sitemap from robots.txt not implemented")

        except requests.exceptions.ConnectionError as err:
            self.logger.debug("%s No connection: %s" % (self.uri, str(err)))

        except AssertionError as err:
            self.logger.debug("%s Error: %s" % (self.uri, str(err)))

        finally:
            session.close()

        return processor



class RSyncParser(HTMLParser):

    def __init__(self):
        super(RSyncParser, self).__init__()
        self.link = None

    def handle_starttag(self, tag, attrs):
        try:
            if "link" == tag:
                attributes = dict(attrs)
                if attributes["rel"] == "resourcesync":
                    self.link = attributes["href"]
        except Exception as err:
            pass # We are not going to analyse corrupt html.

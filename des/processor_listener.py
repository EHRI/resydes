#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os, logging
from des.processor import ProcessorListener
from des.config import Config
from des.location_mapper import DestinationMap

SITEMAP_FOLDER = "sitemaps"


class SitemapWriter(ProcessorListener):

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def event_text_recieved(self, uri, text):
        config = Config()
        netloc = config.boolean_prop(Config.key_use_netloc, False)
        baser_uri, local_path = DestinationMap().find_local_path(uri, netloc=netloc, infix=SITEMAP_FOLDER)
        if local_path is not None:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w") as file:
                file.write(text)
            self.logger.debug("Saved sitemap '%s'" % local_path)
        else:
            self.logger.warn("Could not save sitemap. No local path for %s" % uri)

#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append(".")
try:
    sys.path.insert(0, "../../resync")
except:
    pass
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.resource import Resource

rdm = ResourceDumpManifest()
rdm.parse(uri="http://10.169.32.41:8000/srv/source1/loc2/resourcedump-manifest.xml")
print(type(rdm.parsed_index))
print(rdm.capability)
print(rdm.md_at)
print(rdm.md_completed)
for url in rdm.uris():
    print(url)
for resource in rdm.resources:
    assert type(resource) == Resource
    print(resource.capability)  # None
    print(resource.contents)    # None
    print(resource.lastmod)     # 2013-01-02T13:00:00Z
    print(resource.uri)         # http://example.com/res1
    print(resource.md_at)       # None
    print(resource.mime_type)   # text/html
    print(resource.length)      # 8876
    print(resource.md_completed)# None
    print(resource.ln)          # None
    print(resource._extra)      # None
    print(resource.timestamp)   # 1357131600
    print(resource.path)        # /resources/res1
    print(resource.hash)        # md5:1584abdf8ebdc9802ac0c6a7402c03b6



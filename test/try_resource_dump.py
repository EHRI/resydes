#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append(".")
try:
    sys.path.insert(0, "../../resync")
except:
    pass
from resync.resource_dump import ResourceDump
from resync.resource import Resource

rdump = ResourceDump()
rdump.parse(uri="http://localhost:8000/srv/source1/loc2/resourcedump.xml")
print(type(rdump.parsed_index))
print(rdump.capability)         # resourcedump
print(rdump.md_at)              # 2013-01-03T09:00:00Z
print(rdump.md_completed)       # 2013-01-03T09:04:00Z
print(type(rdump.md_completed))
for url in rdump.uris():
    print(url)
for resource in rdump.resources:
    assert type(resource) == Resource
    print(resource.capability)  # None
    print(resource.contents)    # None
    print(resource.lastmod)     # None
    print(resource.uri)         # http://example.com/resourcedump-part1.zip
    print(resource.md_at)       # None
    print(resource.mime_type)   # application/zip
    print(resource.length)      # 4765
    print(resource.md_completed)# None
    print(resource.ln)          # [{'mime_type': 'application/xml', 'href': 'http://example.com/resourcedump_manifest-part3.xml', 'rel': 'contents'}]
    print(resource._extra)      # None
    print(resource.timestamp)   # None










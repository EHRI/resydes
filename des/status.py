#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from enum import Enum


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
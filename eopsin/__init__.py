#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. include:: ../README.md
"""

import warnings

try:
    from compiler import *
except ImportError as e:
    warnings.warn(ImportWarning(e))

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

__version__ = "0.9.12"
__author__ = "nielstron"
__author_email__ = "n.muendler@web.de"
__copyright__ = "Copyright (C) 2023 nielstron"
__license__ = "MIT"
__url__ = "https://github.com/imperatorlang/opshin"

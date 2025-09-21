#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. include:: ../README.md
"""

import warnings
import importlib.metadata

try:
    __version__ = importlib.metadata.version(__package__ or __name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.24.4"  # fallback version
__author__ = "nielstron"
__author_email__ = "niels@opshin.dev"
__copyright__ = "Copyright (C) 2025 nielstron"
__license__ = "MIT"
__url__ = "https://github.com/OpShin/opshin"


try:
    from .compiler import *
    from .builder import *
    from .util import CompilerError
except ImportError as e:
    warnings.warn(ImportWarning(e))

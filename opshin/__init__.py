#!/usr/bin/env python
"""
.. include:: ../README.md
"""

import importlib.metadata
import warnings

__version__ = importlib.metadata.version(__package__ or __name__)
__author__ = "nielstron"
__author_email__ = "niels@opshin.dev"
__copyright__ = "Copyright (C) 2025 nielstron"
__license__ = "MIT"
__url__ = "https://github.com/OpShin/opshin"


try:
    from .builder import *
    from .compiler import *
    from .util import CompilerError
except ImportError as e:
    warnings.warn(ImportWarning(e))

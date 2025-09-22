"""PyMolFold package initialization"""

from .version import __version__

# These imports must come after __version__
from . import utils
from . import predictors
from .plugin import *

__all__ = [
    "__version__",
    "utils",
    "predictors",
]

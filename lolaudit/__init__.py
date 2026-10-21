from .utils import setup_logging

try:
    from ._build import __version__
except ImportError:
    __version__ = "dev"

"""Job extractors for different scraping strategies."""
from .custom import CustomExtractor
from .clicking import ClickingExtractor
from .iframe import IframeExtractor
from .default import DefaultExtractor

__all__ = [
    'CustomExtractor',
    'ClickingExtractor',
    'IframeExtractor',
    'DefaultExtractor',
]


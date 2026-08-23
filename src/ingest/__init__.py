"""
Ingest module for Agent A.
"""

from src.ingest.live_feed import FeedProvider, CryptoFeedProvider, WeatherFeedProvider, NasaFeedProvider, SyntheticFeedProvider, get_feed_provider
from src.ingest.ingest_agent import LiveIngestAgent

__all__ = [
    "FeedProvider",
    "CryptoFeedProvider",
    "WeatherFeedProvider",
    "NasaFeedProvider",
    "SyntheticFeedProvider",
    "get_feed_provider",
    "LiveIngestAgent"
]

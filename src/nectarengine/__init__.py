"""nectarengine."""

import importlib.metadata
import logging

try:
    __version__ = importlib.metadata.version("nectarengine")
except importlib.metadata.PackageNotFoundError:
    __version__ = "1.0.2"

# Silence httpx logs (defaults to INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

__all__ = [
    "__version__",
    "api",
    "cli",
    "collection",
    "exceptions",
    "market",
    "nftmarket",
    "nft",
    "nfts",
    "nodeslist",
    "pool",
    "poolobject",
    "rpc",
    "tokenobject",
    "tokens",
    "wallet",
]

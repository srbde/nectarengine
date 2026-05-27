"""Utilities for working with the Hive Engine node benchmark metadata."""

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union, overload

import httpx2

_BEACON_HE_NODES_URL = "https://beacon.peakd.com/api/he/nodes"
_BEACON_HE_HISTORY_NODES_URL = "https://beacon.peakd.com/api/heh/nodes"

CACHE_DURATION = 300  # 5 minutes cache

NodeUrlList = List[str]


@dataclass(order=True)
class Node:
    """Represents a Hive Engine node sourced from FlowerEngine metadata."""

    rank: float
    url: str = field(compare=False)
    data: Dict[str, Any] = field(default_factory=dict, compare=False)
    failing_cause: Optional[str] = field(default=None, compare=False)

    def __post_init__(self) -> None:
        cleaned_url = self.url.strip()
        if not cleaned_url:
            raise ValueError("Node url cannot be empty")
        self.url = self._ensure_trailing_slash(cleaned_url)

    def as_url(self) -> str:
        """Return the node endpoint as a normalized URL."""

        return self.url

    def __str__(self) -> str:
        return self.url

    @staticmethod
    def _ensure_trailing_slash(url: str) -> str:
        normalized = url.rstrip("/")
        return f"{normalized}/"


class Nodes(Sequence[Node]):
    """Convenience accessor for FlowerEngine node benchmarks."""

    def __init__(
        self,
        auto_refresh: bool = True,
    ) -> None:
        self._nodes: List[Node] = []
        if auto_refresh:
            self.refresh()

    def refresh(self) -> List[Node]:
        """Reload the node list from the PeakD Beacon API."""
        self._nodes = self.beacon()
        return list(self._nodes)

    def beacon(
        self,
        limit: Optional[int] = None,
        url: str = _BEACON_HE_NODES_URL,
        timeout: int = 15,
    ) -> List[Node]:
        """Fetch Hive Engine nodes from the PeakD Beacon API."""

        return self._fetch_beacon_nodes(url=url, limit=limit, timeout=timeout)

    def beacon_history(
        self,
        limit: Optional[int] = None,
        url: str = _BEACON_HE_HISTORY_NODES_URL,
        timeout: int = 15,
    ) -> List[Node]:
        """Fetch Hive Engine history nodes from the PeakD Beacon API."""

        return self._fetch_beacon_nodes(url=url, limit=limit, timeout=timeout)

    def node_list(self) -> List[Node]:
        """Return the currently cached node list, refreshing if empty."""

        if not self._nodes:
            self.refresh()
        return list(self._nodes)

    def fastest(self, limit: int = 1) -> List[Node]:
        """Return the fastest nodes according to the benchmark ranking."""

        nodes = self.node_list()
        if limit <= 0:
            return []
        return nodes[:limit] if limit < len(nodes) else nodes

    def as_urls(self, limit: Optional[int] = None) -> NodeUrlList:
        """Provide the node URLs, optionally truncated to *limit* entries."""

        nodes = self.node_list()
        if limit is not None:
            nodes = nodes[:limit]
        return [node.as_url() for node in nodes]

    def primary_url(self) -> Optional[str]:
        """Return the highest-ranked node URL or ``None`` if unavailable."""

        nodes = self.node_list()
        return nodes[0].as_url() if nodes else None

    def __len__(self) -> int:
        return len(self.node_list())

    @overload
    def __getitem__(self, index: int) -> Node: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[Node]: ...

    def __getitem__(self, index: Union[int, slice]) -> Union[Node, Sequence[Node]]:
        return self.node_list()[index]

    def __iter__(self) -> Iterator[Node]:
        return iter(self.node_list())

    def _fetch_beacon_nodes(self, url: str, limit: Optional[int], timeout: int) -> List[Node]:
        # Generate cache filename based on URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()
        cache_file = os.path.join(tempfile.gettempdir(), f"nectarengine_cache_{url_hash}.json")
        current_time = time.time()

        payload = None

        # Try to load from disk cache
        if os.path.exists(cache_file):
            try:
                mtime = os.path.getmtime(cache_file)
                if current_time - mtime < CACHE_DURATION:
                    with open(cache_file, "r") as f:
                        payload = json.load(f)
            except (IOError, json.JSONDecodeError):
                pass  # Fallback to fetch

        if payload is None:
            try:
                response = httpx2.get(url, timeout=timeout)
                response.raise_for_status()
                payload = response.json()

                # Save to disk cache
                try:
                    with open(cache_file, "w") as f:
                        json.dump(payload, f)
                except IOError:
                    pass  # Ignore cache write errors
            except httpx2.HTTPError as exc:
                # If fetch fails, try to fallback to expired cache
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, "r") as f:
                            payload = json.load(f)
                    except (IOError, json.JSONDecodeError):
                        raise RuntimeError(f"Unable to reach beacon service: {exc}") from exc
                else:
                    raise RuntimeError(f"Unable to reach beacon service: {exc}") from exc
            except json.JSONDecodeError as exc:
                raise RuntimeError("Beacon API returned invalid JSON payload") from exc

        if not isinstance(payload, list):
            raise RuntimeError("Beacon API returned unexpected structure; expected list")

        beacon_nodes: List[Node] = []
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            endpoint = entry.get("endpoint")
            if not isinstance(endpoint, str) or not endpoint.strip():
                continue

            score = entry.get("score")
            rank = 100.0
            if isinstance(score, (int, float)):
                rank = max(0.0, 100.0 - float(score))

            fail_count = entry.get("fail")
            failing_cause = None
            if isinstance(fail_count, (int, float)) and fail_count > 0:
                failing_cause = f"{int(fail_count)} failed health checks"

            beacon_nodes.append(
                Node(
                    rank=rank,
                    url=endpoint,
                    data=entry,
                    failing_cause=failing_cause,
                )
            )

        beacon_nodes.sort()
        if limit is not None:
            if limit <= 0:
                return []
            return beacon_nodes[:limit]
        return beacon_nodes

import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union, cast

import httpx2

from .nodeslist import Node, Nodes
from .rpc import RPC, RPCError, RPCErrorDoRetry

NodeInput = Union[
    str,
    Node,
    Dict[str, Any],
    Sequence[Union[str, Node, Dict[str, Any]]],
    Nodes,
]
log = logging.getLogger(__name__)

_DEFAULT_RPC_URL = "https://enginerpc.com/"
_DEFAULT_HISTORY_URL = "https://accounts.hive-engine.com/"


def _ensure_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else url + "/"


def _iterable_node_inputs(value: NodeInput) -> Sequence[Union[str, Node, Dict[str, Any]]]:
    if isinstance(value, (list, tuple)):
        return cast(Sequence[Union[str, Node, Dict[str, Any]]], value)
    if isinstance(value, Nodes):
        return list(value)
    return cast(Sequence[Union[str, Node, Dict[str, Any]]], [value])


def _normalize_node_inputs(value: Optional[NodeInput]) -> List[str]:
    if value is None:
        return []

    urls: List[str] = []
    for candidate in _iterable_node_inputs(value):
        if isinstance(candidate, Node):
            urls.append(candidate.as_url())
        elif isinstance(candidate, str):
            cleaned = candidate.strip()
            if cleaned:
                urls.append(cleaned)
        elif isinstance(candidate, dict):
            endpoint = candidate.get("endpoint") or candidate.get("url")
            if isinstance(endpoint, str) and endpoint.strip():
                urls.append(endpoint.strip())
        else:
            raise TypeError(f"Unsupported node input type: {type(candidate)!r}")

    return urls


def _normalize_single_url(value: Optional[NodeInput]) -> Optional[str]:
    urls = _normalize_node_inputs(value)
    if urls:
        return urls[0]
    return None


def _deduplicate_preserve_order(urls: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for url in urls:
        normalized = _ensure_trailing_slash(url.strip())
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered


class _RPCPool:
    def __init__(
        self,
        endpoints: Sequence[str],
        rpc_kwargs: Dict[str, Any],
        per_endpoint_attempts: int = 2,
    ) -> None:
        if not endpoints:
            raise ValueError("At least one RPC endpoint must be provided")
        if per_endpoint_attempts < 1:
            raise ValueError("per_endpoint_attempts must be >= 1")
        self._endpoints = list(endpoints)
        self._rpc_kwargs = rpc_kwargs
        self._current_index = 0
        self._per_endpoint_attempts = per_endpoint_attempts
        self._rpc = self._build_rpc(self._endpoints[self._current_index])

    def _build_rpc(self, url: str) -> RPC:
        return RPC(url=url, **self._rpc_kwargs)

    def _rotate(self) -> None:
        self._current_index = (self._current_index + 1) % len(self._endpoints)
        self._rpc = self._build_rpc(self._endpoints[self._current_index])

    def _execute(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        last_exc: Optional[Exception] = None
        for endpoint_index in range(len(self._endpoints)):
            for attempt in range(1, self._per_endpoint_attempts + 1):
                try:
                    rpc_method = getattr(self._rpc, method_name)
                    return rpc_method(*args, **kwargs)
                except RPCError:
                    raise
                except (RPCErrorDoRetry, httpx2.HTTPError, ValueError) as exc:
                    last_exc = exc
                    log.warning(
                        "RPC endpoint %s failed (attempt %s/%s on node %s/%s): %s",
                        self._endpoints[self._current_index],
                        attempt,
                        self._per_endpoint_attempts,
                        endpoint_index + 1,
                        len(self._endpoints),
                        exc,
                    )
                    if attempt < self._per_endpoint_attempts:
                        continue
                    self._rotate()
                    break
                except Exception as exc:  # pragma: no cover - unexpected error class
                    last_exc = exc
                    log.warning(
                        "Unexpected RPC failure on %s: %s",
                        self._endpoints[self._current_index],
                        exc,
                    )
                    if attempt < self._per_endpoint_attempts:
                        continue
                    self._rotate()
                    break

        raise RuntimeError(
            "All configured Hive Engine nodes are temporarily unavailable right now. "
            "Please try again shortly or provide a custom endpoint."
        ) from last_exc

    def __getattr__(self, name: str) -> Any:
        def caller(*args: Any, **kwargs: Any) -> Any:
            return self._execute(name, *args, **kwargs)

        return caller


class Api:
    """Access the hive-engine API"""

    def __init__(
        self,
        url: Optional[NodeInput] = None,
        rpcurl: Optional[NodeInput] = None,
        history_url: Optional[NodeInput] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        rpc_endpoint_attempts = kwargs.pop("rpc_endpoint_attempts", 2)

        rpc_kwargs = {"user": user, "password": password, **kwargs}

        user_rpc_candidates = _normalize_node_inputs(rpcurl)
        user_url_candidates = _normalize_node_inputs(url)

        endpoint_candidates: List[str] = []
        endpoint_candidates.extend(user_rpc_candidates)
        endpoint_candidates.extend(user_url_candidates)

        nodes_helper: Optional[Nodes] = None

        if not endpoint_candidates:
            nodes_helper = Nodes(auto_refresh=False)
            try:
                beacon_nodes = nodes_helper.beacon()
                endpoint_candidates.extend(node.as_url() for node in beacon_nodes)
            except RuntimeError as exc:
                log.warning("Failed to fetch beacon nodes: %s", exc)

        if not endpoint_candidates:
            endpoint_candidates.append(_DEFAULT_RPC_URL)

        endpoints = _deduplicate_preserve_order(endpoint_candidates)

        rest_base = _normalize_single_url(url)
        if rest_base is None:
            rest_base = endpoints[0]
        self.url = _ensure_trailing_slash(rest_base)

        self.rpc = _RPCPool(
            endpoints=endpoints,
            rpc_kwargs=rpc_kwargs,
            per_endpoint_attempts=rpc_endpoint_attempts,
        )

        history_candidates = _normalize_node_inputs(history_url)
        if not history_candidates:
            try:
                history_nodes = Nodes(auto_refresh=False).beacon_history()
                history_candidates.extend(node.as_url() for node in history_nodes)
            except RuntimeError as exc:
                log.warning("Failed to fetch beacon history nodes: %s", exc)

        if not history_candidates:
            history_candidates.append(_DEFAULT_HISTORY_URL)

        self._history_endpoints = _deduplicate_preserve_order(history_candidates)
        self.history_url = self._history_endpoints[0]
        self._history_retry_limit = 10

    def get_history(
        self, account: str, symbol: str, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """ "Get the transaction history for an account and a token"""
        params = {
            "account": account,
            "limit": limit,
            "offset": offset,
            "symbol": symbol,
        }
        history_endpoint = f"{self.history_url}accountHistory"
        response = httpx2.get(history_endpoint, params=params)
        cnt2 = 0
        while response.status_code != 200 and cnt2 < self._history_retry_limit:
            response = httpx2.get(history_endpoint, params=params)
            cnt2 += 1
        return response.json()

    def get_latest_block_info(self) -> Dict[str, Any]:
        """get the latest block of the sidechain"""
        ret = self.rpc.getLatestBlockInfo(endpoint="blockchain")
        if isinstance(ret, list) and len(ret) == 1:
            return ret[0]
        else:
            return ret

    def get_status(self) -> Dict[str, Any]:
        """gets the status of the sidechain"""
        ret = self.rpc.getStatus(endpoint="blockchain")
        if isinstance(ret, list) and len(ret) == 1:
            return ret[0]
        else:
            return ret

    def get_block_info(self, blocknumber: int) -> Dict[str, Any]:
        """get the block with the specified block number of the sidechain"""
        ret = self.rpc.getBlockInfo({"blockNumber": blocknumber}, endpoint="blockchain")
        if isinstance(ret, list) and len(ret) == 1:
            return ret[0]
        else:
            return ret

    def get_block_range_info(self, start_block: int, count: int) -> List[Dict[str, Any]]:
        """Get information for a consecutive range of blocks.

        This is a convenience wrapper around the ``getBlockRangeInfo`` JSON-RPC
        call. It can fetch up to 1000 blocks in one request and is much more
        efficient than calling :py:meth:`get_block_info` repeatedly.

        Parameters
        ----------
        start_block : int
            The first block number to retrieve.
        count : int
            The number of blocks to retrieve (maximum 1000).

        Returns
        -------
        List[Dict[str, Any]]
            A list where each element is a block dictionary as returned by the
            side-chain node.
        """
        ret = self.rpc.getBlockRangeInfo(
            {"startBlockNumber": start_block, "count": count}, endpoint="blockchain"
        )
        # Some nodes wrap the actual result in an additional list entry; unwrap
        # it to ensure a consistent return type for callers.
        if isinstance(ret, list) and len(ret) == 1 and isinstance(ret[0], list):
            return ret[0]
        return ret

    def get_transaction_info(self, txid: str) -> Dict[str, Any]:
        """Retrieve the specified transaction info of the sidechain"""
        ret = self.rpc.getTransactionInfo({"txid": txid}, endpoint="blockchain")
        if isinstance(ret, list) and len(ret) == 1:
            return ret[0]
        else:
            return ret

    def get_contract(self, contract_name: str) -> Optional[Dict[str, Any]]:
        """Get the contract specified from the database"""
        ret = self.rpc.getContract({"name": contract_name}, endpoint="contracts")
        if isinstance(ret, list) and len(ret) == 1:
            return ret[0]
        else:
            return ret

    def find_one(
        self, contract_name: str, table_name: str, query: Dict[str, Any] = {}
    ) -> Optional[Dict[str, Any]]:
        """Get the object that matches the query from the table of the specified contract"""
        ret = self.rpc.findOne(
            {"contract": contract_name, "table": table_name, "query": query},
            endpoint="contracts",
        )
        # If rpc.findOne wraps the result in a list, unwrap it.
        if isinstance(ret, list) and len(ret) == 1 and isinstance(ret[0], dict):
            return ret[0]
        # If rpc.findOne returns a dictionary directly (expected case for a 'findOne' operation)
        elif isinstance(ret, dict):
            return ret
        # Otherwise, it's not found or an unexpected format
        return None

    def find(
        self,
        contract_name: str,
        table_name: str,
        query: Dict[str, Any] = {},
        limit: int = 1000,
        offset: int = 0,
        indexes: List[str] = [],
    ) -> List[Dict[str, Any]]:
        """Get an array of objects that match the query from the table of the specified contract"""
        ret = self.rpc.find(
            {
                "contract": contract_name,
                "table": table_name,
                "query": query,
                "limit": limit,
                "offset": offset,
                "indexes": indexes,
            },
            endpoint="contracts",
        )
        if isinstance(ret, list) and len(ret) == 1:
            return ret[0]
        else:
            return ret

    def find_all(
        self, contract_name: str, table_name: str, query: Dict[str, Any] = {}
    ) -> List[Dict[str, Any]]:
        """Get an array of objects that match the query from the table of the specified contract"""
        limit = 1000
        offset = 0
        result: List[Dict[str, Any]] = []

        # Initial fetch
        batch = self.find(contract_name, table_name, query, limit=limit, offset=0)
        if not batch:
            return []

        result.extend(batch)

        while len(batch) == limit:
            # Prepare next query with last_id
            last_id = batch[-1].get("_id")
            if not last_id:
                # Fallback to offset if no _id found (shouldn't happen on standard tables)
                offset += limit
                batch = self.find(contract_name, table_name, query, limit=limit, offset=offset)
            else:
                # Merge _id filter into query
                next_query = query.copy()
                next_query["_id"] = {"$gt": last_id}
                batch = self.find(contract_name, table_name, next_query, limit=limit, offset=0)

            if batch:
                result.extend(batch)
            else:
                break

        return result

    def find_many(
        self,
        contract_name: str,
        table_name: str,
        query: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        offset: int = 0,
        last_id: Optional[str] = None,
        indexes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get an array of objects that match the query, supporting last_id for efficient pagination.
        This mirrors the 'findMany' functionality in hiveenginepy.
        """
        if query is None:
            query = {}
        if indexes is None:
            indexes = []
        query_copy = query.copy()
        if last_id:
            if "_id" in query_copy and isinstance(query_copy["_id"], dict):
                query_copy["_id"]["$gt"] = last_id
            elif "_id" in query_copy:
                # _id is already present but not a dict condition, complex case.
                # Assuming simple equality was intended, override with range check?
                # For safety, let's just make it a $gt check if possible or fail if conflict.
                # Standard practice matches hiveenginepy: force the $gt check logic.
                query_copy["_id"] = {"$gt": last_id}
            else:
                query_copy["_id"] = {"$gt": last_id}

        return self.find(
            contract_name,
            table_name,
            query=query_copy,
            limit=limit,
            offset=offset,
            indexes=indexes,
        )

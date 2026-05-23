import unittest
from unittest.mock import Mock, patch

from nectarengine.api import Api, _RPCPool
from nectarengine.nodeslist import Node
from nectarengine.rpc import RPCErrorDoRetry


class Testcases(unittest.TestCase):
    def test_api(self):
        api = Api()
        result = api.get_latest_block_info()
        next_test = result["blockNumber"]
        self.assertTrue(len(result) > 0)

        result = api.get_block_info(next_test - 64000)
        next_test = result["transactions"][0]["transactionId"]
        self.assertTrue(len(result) > 0)

        result = api.get_transaction_info(next_test)
        self.assertTrue(len(result) > 0)

        result = api.get_contract("tokens")
        assert result is not None
        self.assertTrue(len(result) > 0)

        result = api.find("tokens", "tokens")
        self.assertTrue(len(result) > 0)

        result = api.find_one("tokens", "tokens")
        assert result is not None
        self.assertTrue(len(result) > 0)

        result = api.get_history("thecrazygm", "INCOME")
        self.assertTrue(len(result) > 0)


class ApiFallbackTests(unittest.TestCase):
    @patch("nectarengine.api.Nodes")
    @patch("nectarengine.api.RPC")
    def test_api_prefers_beacon_nodes_for_rpc_and_history(self, mock_rpc: Mock, mock_nodes: Mock):
        rpc_nodes_helper = Mock()
        rpc_nodes_helper.beacon.return_value = [
            Node(rank=1.0, url="https://rpc-beacon-1", data={}),
            Node(rank=2.0, url="https://rpc-beacon-2", data={}),
        ]
        rpc_nodes_helper.as_urls.return_value = []

        history_nodes_helper = Mock()
        history_nodes_helper.beacon_history.return_value = [
            Node(rank=1.0, url="https://history-beacon", data={})
        ]

        mock_nodes.side_effect = [rpc_nodes_helper, history_nodes_helper]

        api = Api()

        self.assertEqual(api.url, "https://rpc-beacon-1/")
        self.assertEqual(api.history_url, "https://history-beacon/")
        mock_rpc.assert_called_once()
        self.assertEqual(mock_rpc.call_args.kwargs["url"], "https://rpc-beacon-1/")

    @patch("nectarengine.api.RPC")
    def test_rpc_pool_retries_before_rotating(self, mock_rpc: Mock):
        first_rpc = Mock()
        first_rpc.someMethod.side_effect = [
            RPCErrorDoRetry("temporary"),
            RPCErrorDoRetry("temporary"),
        ]
        second_rpc = Mock()
        second_rpc.someMethod.return_value = "ok"

        mock_rpc.side_effect = [first_rpc, second_rpc]

        pool = _RPCPool(
            endpoints=["https://primary/", "https://secondary/"],
            rpc_kwargs={},
            per_endpoint_attempts=2,
        )

        result = pool.someMethod()

        self.assertEqual(result, "ok")
        self.assertEqual(first_rpc.someMethod.call_count, 2)
        self.assertEqual(second_rpc.someMethod.call_count, 1)

    @patch("nectarengine.api.httpx2.get")
    @patch("nectarengine.api.RPC")
    def test_get_history_retries_history_endpoint(self, mock_rpc: Mock, mock_get: Mock):
        fail_response = Mock()
        fail_response.status_code = 503
        fail_response.json.return_value = {"error": "fail"}

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"data": []}

        mock_get.side_effect = [fail_response, success_response]

        api = Api(url="https://custom-rpc", history_url="https://history.example")
        result = api.get_history("acct", "TOK")

        self.assertEqual(result, {"data": []})
        self.assertEqual(mock_get.call_count, 2)
        called_url = mock_get.call_args_list[0][0][0]
        self.assertEqual(called_url, "https://history.example/accountHistory")
        params = mock_get.call_args_list[0][1]["params"]
        self.assertEqual(params["account"], "acct")

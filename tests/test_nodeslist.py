import unittest
from unittest.mock import Mock, patch

from nectarengine.api import Api
from nectarengine.nodeslist import Node, Nodes


class NodesListTests(unittest.TestCase):
    def setUp(self):
        # Prevent local cache from interfering with tests
        self.exists_patcher = patch("nectarengine.nodeslist.os.path.exists", return_value=False)
        self.exists_patcher.start()
        self.open_patcher = patch("nectarengine.nodeslist.open", unittest.mock.mock_open())
        self.open_patcher.start()

    def tearDown(self):
        self.exists_patcher.stop()
        self.open_patcher.stop()

    def test_node_trailing_slash_and_string_representation(self):
        node = Node(rank=1.0, url="https://foo.example", data={})
        self.assertEqual(node.as_url(), "https://foo.example/")
        self.assertEqual(str(node), "https://foo.example/")

    @patch("nectarengine.nodeslist.httpx2.get")
    def test_refresh_calls_beacon(self, mock_get: Mock):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"endpoint": "https://node-a", "score": 100},
            {"endpoint": "https://node-b", "score": 80},
        ]
        mock_get.return_value = mock_response

        # Auto refresh triggers beacon
        nodes = Nodes(auto_refresh=True)
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].url, "https://node-a/")

    @patch("nectarengine.nodeslist.httpx2.get")
    def test_node_list_triggers_refresh_when_empty(self, mock_get: Mock):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"endpoint": "https://node-a", "score": 100},
        ]
        mock_get.return_value = mock_response

        nodes = Nodes(auto_refresh=False)
        self.assertEqual(len(nodes._nodes), 0)

        # Accessing node_list triggers refresh
        node_list = nodes.node_list()
        self.assertEqual(len(node_list), 1)
        self.assertEqual(mock_get.call_count, 1)

    def test_fastest_and_primary_url_helpers(self):
        # Setup nodes manually to avoid network calls
        nodes = Nodes(auto_refresh=False)
        nodes._nodes = [
            Node(rank=1.0, url="https://fastest.example", data={}),
            Node(rank=2.0, url="https://sluggish.example", data={}),
        ]

        self.assertEqual(nodes.primary_url(), "https://fastest.example/")
        self.assertEqual(
            [node.as_url() for node in nodes.fastest(2)],
            ["https://fastest.example/", "https://sluggish.example/"],
        )
        self.assertEqual(nodes.fastest(0), [])
        self.assertEqual(nodes.fastest(5), nodes.node_list())

    def test_api_accepts_nodes_inputs(self):
        nodes = Nodes(auto_refresh=False)
        nodes._nodes = [
            Node(rank=1.0, url="https://primary.example", data={}),
            Node(rank=2.0, url="https://secondary.example", data={}),
        ]

        with patch("nectarengine.api.RPC") as rpc:
            api_from_nodes = Api(url=nodes)
            self.assertEqual(api_from_nodes.url, "https://primary.example/")
            rpc.assert_called_once_with(url="https://primary.example/", user=None, password=None)

            rpc.reset_mock()
            Api(url=nodes.fastest(2))
            rpc.assert_called_once_with(url="https://primary.example/", user=None, password=None)

            rpc.reset_mock()
            Api(url=[nodes.node_list()[1]])
            rpc.assert_called_once_with(url="https://secondary.example/", user=None, password=None)

    @patch("nectarengine.nodeslist.httpx2.get")
    def test_beacon_fetches_and_sorts_nodes(self, mock_get: Mock):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"endpoint": "https://node-a", "score": 100, "fail": 0},
            {"endpoint": "https://node-b", "score": 80, "fail": 2},
        ]
        mock_get.return_value = mock_response

        nodes = Nodes(auto_refresh=False)
        beacon_nodes = nodes.beacon()

        self.assertEqual(
            [node.as_url() for node in beacon_nodes],
            ["https://node-a/", "https://node-b/"],
        )
        self.assertEqual(beacon_nodes[1].failing_cause, "2 failed health checks")

    @patch("nectarengine.nodeslist.httpx2.get")
    def test_beacon_history_fetches_nodes(self, mock_get: Mock):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"endpoint": "https://history-a", "score": 95, "fail": 0},
        ]
        mock_get.return_value = mock_response

        nodes = Nodes(auto_refresh=False)
        history_nodes = nodes.beacon_history()

        self.assertEqual([node.as_url() for node in history_nodes], ["https://history-a/"])


if __name__ == "__main__":
    unittest.main()

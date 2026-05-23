import hashlib
import os
import tempfile
import time
from unittest.mock import MagicMock, patch
import pytest

from nectarengine.nodeslist import (
    _BEACON_HE_HISTORY_NODES_URL,
    _BEACON_HE_NODES_URL,
    CACHE_DURATION,
    Nodes,
)


@pytest.fixture(autouse=True)
def mock_tempdir(tmp_path):
    with patch("tempfile.gettempdir", return_value=str(tmp_path)), \
         patch("nectarengine.nodeslist.tempfile.gettempdir", return_value=str(tmp_path)):
        yield



def get_cache_file(url):
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(tempfile.gettempdir(), f"nectarengine_cache_{url_hash}.json")


def cleanup_cache(url):
    cache_file = get_cache_file(url)
    if os.path.exists(cache_file):
        os.remove(cache_file)


def setup_function():
    cleanup_cache(_BEACON_HE_NODES_URL)
    cleanup_cache(_BEACON_HE_HISTORY_NODES_URL)


def teardown_function():
    cleanup_cache(_BEACON_HE_NODES_URL)
    cleanup_cache(_BEACON_HE_HISTORY_NODES_URL)


def test_nectarengine_disk_cache():
    """Verify disk caching for NectarEngine nodes."""

    # Setup mocks
    mock_payload = [{"endpoint": "https://mock.he.node", "score": 100}]

    with patch("nectarengine.nodeslist.httpx2.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_payload
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # 1. Fetch standard nodes (Cache Miss)
        print("\n[Step 1] Initial Fetch Standard Nodes")
        nodes_obj = Nodes(auto_refresh=False)
        nodes = nodes_obj.beacon()

        assert len(nodes) == 1
        assert nodes[0].url == "https://mock.he.node/"
        assert mock_get.call_count == 1

        cache_file = get_cache_file(_BEACON_HE_NODES_URL)
        assert os.path.exists(cache_file)
        print(f" -> Cache file created: {cache_file}")

        # 2. Fetch standard nodes again (Cache Hit)
        print("\n[Step 2] Fetch Standard Nodes (Cache Hit)")
        nodes2 = nodes_obj.beacon()
        assert len(nodes2) == 1
        assert mock_get.call_count == 1  # Should NOT increment
        print(" -> API NOT called")

        # 3. Fetch history nodes (Cache Miss - new URL)
        print("\n[Step 3] Initial Fetch History Nodes")
        hist_nodes = nodes_obj.beacon_history()
        assert len(hist_nodes) == 1
        assert mock_get.call_count == 2  # Should increment

        hist_cache_file = get_cache_file(_BEACON_HE_HISTORY_NODES_URL)
        assert os.path.exists(hist_cache_file)
        assert hist_cache_file != cache_file
        print(f" -> History cache file created: {hist_cache_file}")

        # 4. Fetch history nodes again (Cache Hit)
        print("\n[Step 4] Fetch History Nodes (Cache Hit)")
        hist_nodes2 = nodes_obj.beacon_history()
        assert mock_get.call_count == 2  # Should NOT increment
        print(" -> API NOT called")

        # 5. Simulate expired cache
        print("\n[Step 5] Expired Cache")
        old_time = time.time() - (CACHE_DURATION + 10)
        os.utime(cache_file, (old_time, old_time))

        nodes3 = nodes_obj.beacon()
        assert mock_get.call_count == 3  # Should increment
        print(" -> API called (cache expired)")


if __name__ == "__main__":
    try:
        setup_function()
        test_nectarengine_disk_cache()
        print("\nSUCCESS: NectarEngine caching works as expected.")
    except Exception as e:
        print(f"\nFAILURE: {e}")
        import traceback

        traceback.print_exc()
    finally:
        teardown_function()

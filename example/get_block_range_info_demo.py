#!/usr/bin/env python3
"""Demo script for Api.get_block_range_info

Usage
-----
python get_block_range_info_demo.py [start_block] [count]

If no arguments are provided, the script defaults to `start_block=1` and
`count=5`.

Note
----
Public Hive-Engine nodes often disable the `getBlockRangeInfo` call because
it is resource-intensive. If you see an error or an empty response,
try against your own private node or reduce the `count` parameter.
"""

import pprint
import sys
from typing import Any

from nectarengine.api import Api


def main() -> None:
    start_block: int = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    count: int = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    api = Api(url="http://localhost:5000/")  # Optionally pass a custom rpc URL via Api(url="...")

    try:
        blocks: list[dict[str, Any]] = api.get_block_range_info(start_block, count)
    except Exception as exc:
        print(f"Error while calling get_block_range_info: {exc}")
        sys.exit(1)

    print(f"Fetched {len(blocks)} blocks starting at #{start_block}")
    pprint.pprint(blocks)


if __name__ == "__main__":
    main()

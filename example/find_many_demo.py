"""
Example: Using find_many with Query/Cond helpers
"""

import time

from nectarengine.api import Api


def run():
    api = Api()

    print("Fetching tokens with precision > 0 using find_many...")

    # Use standard dictionary for querying
    query = {"precision": {"$gt": 0}}

    # Demonstrate manual pagination with find_many via last_id
    # (Note: find_all does this recursion internally, but find_many allows explicit control)

    limit = 50
    last_id = None
    total_found = 0

    while True:
        print(f"Fetching page with limit={limit}, last_id={last_id}...")

        # find_many automatically injects {"_id": {"$gt": last_id}} if last_id is provided
        batch = api.find_many(
            contract_name="tokens", table_name="tokens", query=query, limit=limit, last_id=last_id
        )

        if not batch:
            print("No more results.")
            break

        count = len(batch)
        total_found += count

        # Determine last_id for next page
        # Hive Engine results usually have an "_id" field (integer or string)
        last_item = batch[-1]
        last_id = last_item.get("_id")

        print(f"  Got {count} items. Last ID: {last_id}")

        # Print a few symbols from this batch
        symbols = [t.get("symbol") for t in batch[:5]]
        print(f"  Sample: {symbols}")

        if count < limit:
            print("Reached end of data (batch smaller than limit).")
            break

        # Be nice to the API
        time.sleep(0.5)

    print(f"Done. Total tokens found: {total_found}")


if __name__ == "__main__":
    run()

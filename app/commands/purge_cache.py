import json
import sys

from app.storage.cache_store import CacheStore


def main() -> None:
    store = CacheStore()
    result = store.purge_unindexed()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["removed"] > 0:
        sys.exit(0)


if __name__ == "__main__":
    main()

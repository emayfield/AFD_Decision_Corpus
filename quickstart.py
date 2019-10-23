import time
from server import DebateServer

if __name__ == "__main__":
    normalized = 2
    config = {
        "extractors": ["TALLY"],
        "normalized": normalized,
        "strict_discussions": True,
        "source": "afd_2019_full_policies.json",
        "cached_influences": False
    }

    start = time.time()
    server = DebateServer(config)
    end = time.time()
    print(f"{end-start} seconds to initialize corpus (including download if this is first run).")

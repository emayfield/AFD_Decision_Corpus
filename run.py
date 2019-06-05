from server import DebateServer
from scratchpad import dry_run
import time

if __name__ == "__main__":
    for i in range(1,21):
        config = {
            "extractors": ["TALLY"],
            "normalized": 3,
            "strict_discussions": True,
            "source": "afd_2019_randomized_offset_{}.json".format(i)
        }
        server = DebateServer(config)
        start = time.time()
        dry_run(server)
        end = time.time()
        print("{} seconds for processing request.".format((end-start)))

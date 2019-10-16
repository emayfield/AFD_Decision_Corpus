from server import DebateServer
from scratchpad import dry_run
import time

if __name__ == "__main__":
    for i in range(5,20):
        config = {
            "extractors": ["TALLY", "BERT"],
            "normalized": 3,
            "strict_discussions": True,
            "source": "jsons/afd_2019_randomized_offset_{}.json".format(i)
        }
        server = DebateServer(config)
        start = time.time()
        dry_run(server)
        end = time.time()
        print("{} seconds for processing request.".format((end-start)))

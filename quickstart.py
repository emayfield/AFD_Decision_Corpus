import time
from server import DebateServer

if __name__ == "__main__":
    normalized = 2
    """
    This dictionary defines the behavior of the Deletion corpus code. It has the following possible keys:

    "extractors": Points to a list of features to extract for each instance in a machine learning task.
                  Features from each extractor are concatenated at training time. Available extractors:
                    "TALLY": Extracts count and percent voting features from each text.
                    "VOLUME": Extracts raw features like total time elapsed and number of votes.

    """
    config = {
        "extractors": ["VOLUME"],
        "normalized": normalized,
        "strict_discussions": True,
        "source": "afd_2019_full_policies.json",
        "cached_influences": False
    }

    start = time.time()
    server = DebateServer(config)
    end = time.time()
    print(f"{end-start:2.2f} seconds to initialize corpus (including download if this is first run).")

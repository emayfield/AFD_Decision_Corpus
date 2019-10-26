import time
from server import DebateServer
from endpoints.identity.success import SuccessAnalysis
from endpoints.identity.survival import SurvivalAnalysis

if __name__ == "__main__":
    normalized = 2
    config = {
        "extractors": ["TALLY"],
        "normalized": normalized,
        "strict_discussions": True,
        "source": "afd_2019_full_policies.json",
        "cached_influences": False
    }
    analyses = [SurvivalAnalysis()]
    initialize = time.time()
    server = DebateServer(config)
    start = time.time()

    for analysis in analyses:
        analysis.run(server, normalized)

    end = time.time()
    print(f"{(start-initialize)} to initialize, {(end-start)} seconds for processing request.")

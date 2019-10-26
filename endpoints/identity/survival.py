from endpoints.identity.tools import get_strict_discussions, generate_single_profile, check_success, summarize_log
from collections import defaultdict

class SurvivalAnalysis():

    """
    Partitions our users into subsets based on a particular variable or variables of interest.
    Returns the categorical label for a particular user, given a set of details about that user.
    """
    def key(self, details):
        keyA = "unknown"
        gender = ""
        first_time = ""
        enfranchised = ""
        tenure_at = "UNK"
        if "tenure_at" in details.keys():
            tenure_at = details["tenure_at"]
        if "gender" in details.keys():
            gender = details["gender"]
        if "first_time" in details.keys():
            if details["first_time"]:
                first_time = "newcomer"
            else:
                first_time = "veteran"
        if "enfranchised" in details.keys():
            if details["enfranchised"]:
                enfranchised = "Wikipedian"
        keyA = f"{gender} {enfranchised} {tenure_at}"
        return keyA

    def run(self, server, normalized):
        # We first analyze only conversations that have one 
        code, discussions = get_strict_discussions(server)
        suffix = "success"
        bucketed_success_log = defaultdict(lambda: [])
        bucketed_dropout_log = defaultdict(lambda: [])

        all_user_contribs = defaultdict(lambda: [])
        for disc_id in discussions:
            code, contrib_ids = server.discussions.get_contributions(disc_id)
            if disc_id % 1000 == 0:
                print("Processing discussion {}".format(disc_id))

            user_participation = defaultdict(lambda: [])
            for i, contrib_id in enumerate(contrib_ids):
                code, user_id = server.util.get_user_id(contrib_id)
                user_participation[user_id].append(contrib_id)
            for user in user_participation:
                all_user_contribs[user].append(user_participation[user])

        for user in all_user_contribs.keys():
            details = generate_single_profile(server, user_id)
            this_user_lifetime = server.users.get_contributions(user)
            last_contrib_id = this_user_lifetime[-1]
            for i, discussion_set in enumerate(all_user_contribs[user]):
                local_details = details.copy()
                success = check_success(server, discussion_set)
                dropout = last_contrib_id in discussion_set
                min_tenure = 99999999
                for contrib in discussion_set:
                    if contrib in this_user_lifetime:
                        ix = this_user_lifetime.index(contrib)
                        min_tenure = min(ix, min_tenure)
                if min_tenure < 99999999:
                    details["tenure_at"] = min_tenure
                key = self.key(details)
                bucketed_success_log[key].append(success)
                bucketed_dropout_log[key].append(dropout)

        summarize_log(bucketed_dropout_log)
        summarize_log(bucketed_dropout_log)
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
        first_time = "newcomer" if "first_time" in details.keys() and details["first_time"] else "veteran"
        enfranchised = "wikipedian" if "enfranchised" in details.keys() and details["enfranchised"] else "amateur"
        tenure_at = "UNK"
        if "tenure_at" in details.keys():
            tenure_at = details["tenure_at"]
            if tenure_at > 100:
                tenure_at = ">100"
        if "gender" in details.keys():
            gender = details["gender"]
        keyA = [gender, enfranchised, tenure_at]
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
                code, user = server.util.get_user_id(contrib_id)
                user_participation[user].append(contrib_id)
            for user in user_participation:
                all_user_contribs[user].append(user_participation[user])

        dropouts = 0
        non_dropouts = 0
        key_strings = {}
        for user in all_user_contribs.keys():
            details = generate_single_profile(server, user)
            code, this_user_lifetime = server.users.get_contributions(user)
            if this_user_lifetime is None or len(this_user_lifetime) == 0:
                code, name = server.users.get_name(user)
                print(f"User {user} name {name} has no history.")
            else:
                last_contrib_id = this_user_lifetime[-1]
                for i, discussion_set in enumerate(all_user_contribs[user]):
                    local_details = details.copy()
                    success = check_success(server, discussion_set)

                    # These next two things not currently being calculated properly:
                    # Tenure at post i
                    # Dropout vs. stay
                    dropout = last_contrib_id in discussion_set
                    if dropout:
                        dropouts += 1
                    else:
                        non_dropouts += 1
                        
                    min_tenure = 99999999
                    for contrib in discussion_set:
                        if contrib in this_user_lifetime:
                            ix = this_user_lifetime.index(contrib)
                            min_tenure = min(ix, min_tenure)
                    if min_tenure < 99999999:
                        details["tenure_at"] = min_tenure

                    # Code works fine from this point forward.
                    key_list = self.key(details)
                    bucketed_success_log[str(key_list)].append(success)
                    bucketed_dropout_log[str(key_list)].append(dropout)
                    key_strings[str(key_list)] = key_list

        summarize_log("dropout", key_strings, bucketed_dropout_log)
        summarize_log("success", key_strings, bucketed_success_log)
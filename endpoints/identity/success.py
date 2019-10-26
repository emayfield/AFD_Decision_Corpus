from endpoints.identity.tools import get_strict_discussions, check_success, generate_single_profile

from collections import defaultdict

class SuccessAnalysis():

    """
    Partitions our users into subsets based on a particular variable or variables of interest.
    Returns the categorical label for a particular user, given a set of details about that user.
    """
    def key(self, details):
        keyA = "unknown"
        gender = ""
        first_time = ""
        enfranchised = ""
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
        keyA = "{} {} {}".format(gender, enfranchised, first_time)
        return keyA


    def run(self, server, normalized):
        # We first analyze only conversations that have one 
        code, discussions = get_strict_discussions(server)
        suffix = "success"
        bucketed_success_log = defaultdict(lambda: [])
        for disc_id in discussions:
            code, contrib_ids = server.discussions.get_contributions(disc_id)
            if disc_id % 1000 == 0:
                print("Processing discussion {}".format(disc_id))

            contribs_to_users = {}
            users_to_contribs = defaultdict(lambda: [])
            for i, contrib_id in enumerate(contrib_ids):
                code, user_id = server.util.get_user_id(contrib_id)
                code, timestamp = server.util.get_timestamp(contrib_id)

                contribs_to_users[contrib_id] = user_id
                users_to_contribs[user_id].append(contrib_id)

            for user_id in users_to_contribs:
                details = generate_single_profile(server, user_id)
                """Produces two first-time levels, true and false."""
                code, first_time = server.util.first_time_user(server, user_id, disc_id)
                if code == 200:
                    details["first_time"] = first_time

                check_success(server, users_to_contribs[user_id])
                key = self.key(details)
                bucketed_success_log[key].append(success)

        success_rates = {}
        for key in bucketed_success_log:
            positive = 0
            total = 0
            for event in bucketed_success_log[key]:
                if event:
                    positive += 1
                total += 1
            rate = (positive/total)
            print(f"{key} {positive} / {total} = {rate}")
            success_rates[key] = rate

        return success_rates

import time

class AnalysisEndpoint:

    def __init__(self, server):
        self.server = server

    """
    Params: Contribution ID (outcome, nomination, vote, comment) to test.
    Returns: 200, one of ["Win", "Lose", "Unclear", "Outcome", "Nonvoting"] under the following conditions:
                    "Outcome"       : contribution ID begins with 3 (outcome ID)
                    "Vote Unclear"  : contribution ID begins with 4 (vote) and vote == "Other" or outcome == "Other
                    "Vote Win"      : contribution ID begins with 4 (vote), vote label is "Keep" or "Delete", and vote label == outcome label
                    "Vote Lose"     : contribution ID begins with 4 (vote), in any other case
                    "Nonvoting"     : contribution ID begins with 5 (Comment)
                    "Nom Win"       : contribution ID begins with 6 (nomination) and outcome value is "Delete"
                    "Nom Lose"      : contribution ID begins with 6 (nomination) and outcome value is "Keep"
                    "Nom Unclear"   : contribution ID begins with 6 (nomination) and outcome value is "Other"
         or  404, None   : contribution ID does not have an associated discussion 
                    OR   : this discussion ID has no outcome ID
         or  500, None if something else went wrong.

        TODO - HONESTLY this is old code and should be scrapped.
    """
    def get_success_status(self, contrib_id):
        try:
            is_vote = self.server.util.is_vote(contrib_id)
            is_outcome = self.server.util.is_outcome(contrib_id)
            is_comment = self.server.util.is_comment(contrib_id)
            is_nomination = self.server.util.is_nomination(contrib_id)
            if is_outcome:
                return 200, "Outcome"
        
            disc_id = -1
            if is_vote:
                code, disc_id = self.server.votes.get_discussion_id(contrib_id)
            if is_comment:
                code, disc_id = self.server.comments.get_discussion_id(contrib_id)
            if is_nomination:
                code, disc_id = self.server.nominations.get_discussion_id(contrib_id)
            if disc_id == -1:
                return 404, None

            code, outcome_id = self.server.discussions.get_outcome_id(disc_id)
            if code == 404:
                return 404, None
            code, outcome_label = self.server.outcomes.get_label(outcome_id)
            if is_vote:
                code, vote_label = self.server.votes.get_label(contrib_id)
                if vote_label == "Other" or outcome_label == "Other":
                    return 200, "Vote Unclear"
                else:
                    if vote_label == outcome_label:
                        return 200, "Vote Win"
                    else:
                        return 200, "Vote Lose"
            elif is_comment:
                return 200, "Nonvoting"
            elif is_nomination:
                if outcome_label == "Other":
                    return 200, "Nom Unclear"
                elif outcome_label == "Keep":
                    return 200, "Nom Lose"
                elif outcome_label is not None:
                    return 200, "Nom Win"
                else:
                    return 500, None
            else:
                return 500, None
        except:
            return 500, None
    
    def extract_features(self):
        code, disc_ids = self.server.discussions.get_all()
        instance_to_disc = {}
        for disc_id in disc_ids:
            code, inst_id = self.server.instances.post_instance(disc_id, 9999999999)
            instance_to_disc[inst_id] = disc_id
        code, instance_ids = self.server.instances.get_all()
        print("Created {} discussion instances.".format(len(instance_ids)))
        for instance_id in instance_ids:
            self.server.extractors[0].extract_features(instance_id, 9999999999)

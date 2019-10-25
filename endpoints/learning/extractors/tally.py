
"""
Feature extractor for the raw vote tallies of a discussion. Simple! Effective! 
"""
class TallyEndpoint:
    
    def __init__(self, server):
        self.server = server

    """
    Returns: 200, feature names (list) for vote counts (both % and #).
    Right now just the 10 features of # and % for each of five vote labels is frustratingly effective.
    """
    def feature_names(self):
        names = []
        for label in ["Keep", "Delete","Merge","Redirect","Other"]:
            count_feature = "Count {}".format(label)
            percent_feature = "Percent {}".format(label)
            names.extend([count_feature,percent_feature])
        return 200, names

    """
    Params: Instance ID for a single discussion and timestamp to extract features from.
    Returns: 200, vote tally features (always a subset of feature names above)
        or   500, None if something went wrong.

    Format: dict of feature name (string) to feature value (int or float)
    """
    def extract_features(self, instance_id, vote_timestamp, contrib_ids=None):
        try:
            code, discussion_id = self.server.instances.get_discussion_id(instance_id)
            if contrib_ids is None:
                code, contrib_ids = self.server.discussions.get_contributions_at_time(discussion_id, vote_timestamp)

            code, title = self.server.discussions.get_title(discussion_id)
            x = {}

            vote_counts = defaultdict(int)
                
            for c in contrib_ids:
                if(self.server.util.is_vote(c)):
                    code, vote_label = self.server.votes.get_label(c, normalized=self.server.config["normalized"])
                    if code == 200:
                        if vote_label in vote_counts.keys():
                            vote_counts[vote_label] = vote_counts[vote_label] + 1

            code, vote_tally = self.get_normalized_tally(vote_counts)
            for label in ["Keep", "Delete", "Merge", "Redirect", "Other"]:
                count_feature = "Count {}".format(label)
                if label in vote_counts.keys():
                    x[count_feature] = vote_counts[label]
                else:
                    x[count_feature] = 0
                percent_feature = "Percent {}".format(label)
                if label in vote_tally.keys():
                    x[percent_feature] = vote_tally[label]
                else:
                    x[percent_feature] = 0
            return 201, x
        except Exception as e:
            print("Dropping an instance {}".format(instance_id))
            print(e)
            return 500, None


    """
    Takes a tally and converts it into a probability distribution that sums to 1.
    Params: dict of keys to numeric values.
    Returns: 200, dict of normalized values for each key
        or   500, None if something went wrong.
    """
    def get_normalized_tally(self, tally):
        try:
            total = 0.0
            for key in tally.keys():
                total += tally[key]
            norm_tally = {k:(tally[k]/total) for k in tally.keys()}
            return 200, norm_tally
        except:
            return 500, None

    """
    Params: Two tally dicts to combine
    Returns: 200, Combined tally dicts, where shared keys equal the sum of tallies in each dict.
        or   500, None if something went wrong.
    """
    def get_combined_tally(self, base_tally, new_tally):
        try:
            combined_tally = {}
            for key in base_tally:
                combined_tally[key] = base_tally[key]
            for key in new_tally:
                if key in combined_tally.keys():
                    combined_tally[key] = combined_tally[key] + new_tally[key]
                else:
                    combined_tally[key] = new_tally[key]
            return 200, combined_tally
        except:
            return 500, None
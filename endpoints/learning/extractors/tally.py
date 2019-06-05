
"""
Feature extractor for the raw vote tallies of a discussion. Simple! Effective! 
"""
class TallyEndpoint:
    
    def __init__(self, server):
        self.server = server

    """
    Returns: 200, feature names (list) for timestamp-related features and vote counts (both % and #).
    Right now just the 10 features of # and % for each of five vote labels is frustratingly effective.
    """
    def feature_names(self):
        names = []
        """
        Time-based features
        """
#            names.append("Time Elapsed")

        """
        Vote-based features
        """
#            names.append("Total Votes")
#            names.append("Total Comments")
        for label in ["Keep", "Delete","Merge","Redirect","Other"]:
            count_feature = "Count {}".format(label)
            percent_feature = "Percent {}".format(label)
            names.extend([count_feature,percent_feature])
        return 200, names

    """
    Params: Instance ID for a single discussion and timestamp to extract features from.
    Returns: 200, vote tallies and timestamp-related features (always a subset of feature names above)
        or   500, None if something went wrong.

    Format: dict of feature name (string) to feature value (int or float)
    """
    def extract_features(self, instance_id, vote_timestamp, contrib_ids=None):
        try:
            code, discussion_id = self.server.instances.get_discussion_id(instance_id)
            if contrib_ids is None:
                code, contrib_ids = self.server.discussions.get_contributions_at_time(discussion_id, vote_timestamp)
            code, times_tuple = self.server.discussions.get_timestamp_range(discussion_id)

            code, title = self.server.discussions.get_title(discussion_id)

            beginning, end = 0, 0
            if times_tuple is not None:
                beginning, end = times_tuple

            x = {}
            """
            Time-based features
            """
            if end is not None:
                x["Time Elapsed"] = min(end, vote_timestamp)
            else:
                x["Time Elapsed"] = 0

            """
            Vote-based features
            """
            vote_counts = {}
            total_votes = 0
            total_comments = 0
                
            for c in contrib_ids:
                if(self.server.util.is_vote(c)):
                    code, vote_label = self.server.votes.get_label(c, normalized=self.server.config["normalized"])
                    if code == 200:
                        total_votes += 1
                        if vote_label in vote_counts.keys():
                            vote_counts[vote_label] = vote_counts[vote_label] + 1
                        else:
                            vote_counts[vote_label] = 1
                if(self.server.util.is_comment(c)):
                    total_comments += 1
            x["Total Votes"] = total_votes
            x["Total Comments"] = total_comments

            code, vote_tally = self.server.math.get_normalized_tally(vote_counts)
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
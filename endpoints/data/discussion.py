
class DiscussionEndpoint():

    def __init__(self):
        self.discussions = {}

    """
    Params: JSON representation of a discussion.
    Returns: 201, discussion ID of the created JSON 
        or   500, None if something went wrong.
    """
    def post_discussion(self, discussion_json):
        disc = Discussion(discussion_json)
        try:
            disc_id = disc.id
            self.discussions[disc_id] = disc
            return 201, disc_id
        except:
            return 500, None

    """
    Params: Discussion ID to access, new contribution ID (nomination, outcome, vote, comment), timestamp of that contribution.
    Returns: 200, same discussion ID if the contribution and timestamp was successfully stored.
        or   500, None if something went wrong.
    """
    def put_contribution(self, discussion_id, contribution_id, timestamp):
        try:
            if discussion_id in self.discussions.keys():
                disc = self.discussions[discussion_id]
                if timestamp is None:
                    timestamp = -1
                disc.contributions.append((contribution_id, timestamp))
                contrib_code = str(contribution_id)[0]
                if contrib_code == "3":
                    disc.outcome_id = contribution_id
                self.discussions[discussion_id] = disc
                return 200, discussion_id
            else:
                return 404, None
        except:
            return 500, None


    """
    Call after corpus is loaded. Sorts all users' contribution lists in chronological order.
    """
    def put_sort_contributions(self):
        try:
            for discussion_id in self.discussions.keys():
                disc = self.discussions[discussion_id]
                disc.contributions = list(sorted(disc.contributions, key=lambda x:x[1]))
            num_discussions = len(self.discussions.keys())
            print("Sorted {} discussions".format(num_discussions))
            return 200, num_discussions
        except Exception as e:
            print("ERROR: {}".format(e))
            return 500, None

    """
    Params: None
    Returns: 200, All discussion IDs in this corpus
        or   500, None if something went wrong
    """
    def get_all(self):
        try:
            return 200, self.discussions.keys()
        except:
            return 500, None

    """
    Params: ID (int) of discussion to look up.
    Returns: 200, One single Discussion object if found
        or   404, None if discussion ID does not exist.
        or   500, None if something has gone wrong.
    """
    def get_by_id(self, disc_id):
        try:
            if disc_id in self.discussions.keys():
                return 200, self.discussions[disc_id]
            else:
                return 404, None
        except:
            return 500, None
    
    """
    Params: Discussion ID (int) to look up.
    Returns: 200, title (string) of the discussion with that ID
        or   404, None if that discussion ID does not exist
        or   500, None if something else went wrong.
    """
    def get_title(self, disc_id):
        try:
            if disc_id in self.discussions.keys():
                return 200, self.discussions[disc_id].title
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: Discussion ID (int) to look up.
    Returns: 200, all extracted timestamps (list) from votes, comments, and outcomes from this discussion ID.
        or   404, None if that discussion ID does not exist
        or   500, None if something else went wrong.
    """
    def get_timestamps(self, disc_id):
        try:
            if disc_id in self.discussions.keys():
                return 200, [x[1] for x in self.discussions[disc_id].contributions]
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: Discussion ID (int) to look up.
    Returns: 200, (earliest, latest) (ints) tuple for timestamps at range of the discussion, among extracted votes, comments, and outcome.
        or   404, None if that discussion ID does not exist or no timestamps were extracted
        or   500, None if something else went wrong.
    """
    def get_timestamp_range(self, disc_id):
        try:
            range = None
            if disc_id in self.discussions.keys():
                code, times = self.get_timestamps(disc_id)
                if len(times) > 0:
                    earliest = min(times)
                    latest = max(times)
                    return 200, (earliest, latest)
                else:
                    return 404, None
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: Discussion title (string) to look up
    Returns: 200, discussion ID (int) if title is found
        or   404, None if that title does not exist
        or   500, None if something else went wrong.
    """
    def get_id_by_title(self, input_title):
        try:
            for id in self.discussions.keys():
                code, test_title = self.get_title(id)
                if test_title == input_title:
                    return 200, id
            return 404, None
        except:
            return 500, None

    """
    Params: start timestamp; end timestamp
    Returns: 200, List of all Discussion IDs that occurred within the stated range.
             If not strict (default), only the *last* captured timestamp must occur within the stated range.
             If strict, *all* timestamps must occur within the stated range.
        or   500, None if something else went wrong.
    """
    def get_discussions_by_timestamps(self, start=0, end=2145916800, strict=False):
        try:
            out_ids = []
            for disc_id in self.discussions.keys():
                code, times = self.get_timestamp_range(disc_id)
                if code == 200:
                    disc_first = times[0]
                    disc_last = times[1]
                    if disc_last > start and disc_last < end:
                        if not strict or (disc_first > start and disc_last < end):
                            out_ids.append(disc_id)
            return 200, out_ids
        except:
            return 500, None
    
    """
    Params: ID (int) of a particular discussion to look up
    Returns: 200, unique outcome ID associated with that discussion
        or   404, None if no outcome ID exists for that discussion
                    OR if that discussion ID does not exist
        or   500, None if something else went wrong.
    
    For now we assume that there are either 0 or 1 outcomes for each discussion ID.
    """
    def get_outcome_id(self, disc_id):
        try:
            if disc_id in self.discussions.keys():
                outcome_id = self.discussions[disc_id].outcome_id
                if outcome_id == -1:
                    return 404, None
                else:
                    return 200,outcome_id
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a discussion to look up.
    Returns: 200, list of contribution IDs in that discussion.
        or   404, None if that discussion ID does not exist
        or   500, None if something else went wrong.
    """
    def get_contributions(self, disc_id):
        try:
            code, disc = self.get_by_id(disc_id)
            if code == 200:
                contribs = disc.contributions
                return 200, [c[0] for c in contribs]
            else:
                return code, None
        except:
            return 500, None

    """
    Params: ID (int) of a discussion to look up, timestamp (int) to evaluate a discussion at.
    Does *not* include the contributions (if any) at exactly that timestamp.
    Returns: 200, list of contribution IDs that had occured by that timestamp
        or   404, None if no discussion with that ID exists
        or   500, None if something went wrong.
    """
    def get_contributions_at_time(self, disc_id, timestamp):
        try:
            code, disc = self.get_by_id(disc_id)
            if code == 200:
                contribs = disc.contributions
                filtered = [x[0] for x in filter(lambda c: c[1] is not None and c[1] < timestamp, contribs)]
                return 200, filtered
            else:
                return code, None
        except:
            return 500, None

class Discussion:
    def __init__(self, disc_json):
        self.id = -1
        self.title = None
        self.contributions = []
        self.outcome_id = -1
        if "ID" in disc_json.keys():
            self.id = disc_json["ID"]
        if "Title" in disc_json.keys():
            self.title = disc_json["Title"]
    
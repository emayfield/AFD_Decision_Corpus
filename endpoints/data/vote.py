
import re

class VoteEndpoint:

    def __init__(self):
        self.votes = {}

    """
    Params: JSON representation of a vote.
    Returns: 201, ID of the created Vote object.
        or   500, None if something went wrong.
    """
    def post_vote(self, vote_json):
        vote = Vote(vote_json)
        try:
            vote_id = vote.id
            self.votes[vote_id] = vote
            return 201, vote_id
        except:
            return 500, None
            
    """
    Params: none
    Returns: 200, All known Vote IDs (list) in the corpus
        or   500, None if something went wrong.
    """
    def get_all(self):
        try:
            return 200, self.votes.keys()
        except:
            return 500, None

    """
    BEGIN LOOKUPS BY SINGLE VOTE ID
    """

    """
    Params: ID (int) of a particular vote to look up
    (note: NOT the discussion ID. Use get_by_discussion_id for that)
    Returns: 200, One single Vote object if found
        or   404, None if vote ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_by_id(self, vote_id):
        try:
            if vote_id in self.votes.keys():
                return 200, self.votes[vote_id]
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a particular vote to look up, normalization factor from:
        0: Raw text of the vote from the original AfD.
        1: Full set of common keywords discovered in the raw text.
        2: Shrink down to "Keep", "Delete", "Other", where "Delete" supercedes "Keep" in the rare case both are present.
        3: Shrink down to "Keep", "Delete" as described in NLP+CSS paper.
    Returns: 200, normalized vote label (string in [Keep, Delete, Merge, Redirect, Other]) if found
        or   404, None if vote ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_label(self, vote_id, normalized):
        try:
            if vote_id in self.votes.keys():
                label = ""
                if normalized == 0:
                    label = self.votes[vote_id].raw_label
                elif normalized == 1 or normalized == 2:
                    label = self.votes[vote_id].label
                    if normalized == 2:
                        minimal_label = "Other"
                        if "merge" in label:
                            minimal_label = "Merge"
                        if "redirect" in label:
                            minimal_label = "Redirect"
                        if "keep" in label:
                            minimal_label = "Keep"
                        if "delete" in label:
                            minimal_label = "Delete"
                        label = minimal_label
                elif normalized == 3:
                    code, actual = self.get_label(vote_id, normalized=2)
                    if actual in ["Merge", "Redirect"]:
                        actual = "Delete"
                    if actual in ["Other"]:
                        actual = "Keep"
                    label = actual
                return 200, label
            else:
                return 404, None
        except:
            return 500, None
      
    """
    Params: ID (int) of a particular vote to look up
    Returns: 200, user_id (int) if that vote has a user_id
        or   404, None if vote ID does not exist.
        or   500, None if something went wrong.
    """
    def get_user_id(self, vote_id):
        try:
            if vote_id in self.votes.keys():
                return 200, self.votes[vote_id].user_id
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a particular vote to look up
    Returns: 200, rationale text (string) if found
        or   404, None if vote ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_rationale(self, vote_id):
        try:
            if vote_id in self.votes.keys():
                return 200, self.votes[vote_id].rationale
            else:
                return 404, None
        except:
            return 500, None
    
    """
    Params: ID (int) of a particular vote to look up
    Returns: 200, timestamp since epoch (int) if found
        or   404, None if vote ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_timestamp(self, vote_id):
        try:
            if vote_id in self.votes.keys():
                return 200, self.votes[vote_id].timestamp
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a particular vote to look up
    Returns: 200, discussion ID (int) if found
        or   404, None if vote ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_discussion_id(self, vote_id):
        try:
            if vote_id in self.votes.keys():
                return 200, self.votes[vote_id].discussion_id
            else:
                return 404, None
        except:
            return 500, None

    """
    END LOOKUPS BY SINGLE VOTE ID

    BEGIN LOOKUPS BY OTHER VARIABLES
    """
    
    """
    Params: A single user ID (int)
    Returns: 200, All known vote IDs from a single user. (list)
        or   500, None if something went wrong.
    """
    def get_votes_by_user(self, user_id):
        try:
            user_vote_ids = list(filter(lambda x: self.votes[x].user_id == user_id, self.votes.keys()))
            return 200, user_vote_ids
        except:
            return 500, None

    """
    Params: A single discussion ID (int)
    Returns: 200, All known vote IDs in a single discussion. (list)
        or   500, None if something went wrong.
    """
    def get_votes_by_discussion(self, disc_id):
        try:
            discussion_vote_ids = list(filter(lambda x: self.votes[x].discussion_id == disc_id, self.votes.keys()))
            return 200, discussion_vote_ids
        except:
            return 500, None

    """
    NOTE: Right now this must be the *beginning* of a chain of filters (it selects from the whole corpus, not a set of IDs passed in)
    Params: start timestamp; end timestamp
    Returns: 200, Subset of votes from input list that occurred between timestamps (inclusive)
        or   500, None if something else went wrong.
    """
    def get_votes_by_timestamps(self, start=0, end=2145916800):
        try:
            vote_ids = list(filter(lambda x: start <= self.votes[x].timestamp <= end, self.votes.keys()))
            return 200, vote_ids
        except:
            return 500, None
    """
    END LOOKUPS BY OTHER VARIABLES

    BEGIN CALCULATION FUNCTIONS
    """

    """
    Params: List of vote_ids to count up (contribution IDs that are not votes are ignored)
    Returns: 200, dict from label to count
        or   500, None if something else went wrong.
    """
    def get_vote_tally(self, vote_ids, normalized):
        try:
            tally = {}
            for vote_id in vote_ids:
                if vote_id in self.votes.keys():
                    code, normalized_label = self.get_label(vote_id, normalized=normalized)
                    if normalized_label in tally.keys():
                        tally[normalized_label] = tally[normalized_label] + 1
                    else:
                        tally[normalized_label] = 1
            return 200, tally
        except:
            return 500, None

    """
    Params: One Discussion ID
    Returns: 200, Tally of vote counts in that discussion.
        or   500, None if something else went wrong.
    """
    def get_vote_tally_by_discussion(self, disc_id, normalized):
        try:
            code, discussion_vote_ids = self.get_votes_by_discussion(disc_id)
            if code == 200:
                code, tally = self.get_vote_tally(discussion_vote_ids, normalized)
                if code == 200:
                    return 200, tally
            return code, None
        except:
            return 500, None

    """
    Params: One User ID
    Returns: Dict of {
        Normalized vote : Vote count
    }
    """
    def get_vote_tally_by_user(self, user_id, normalized):
        try:
            code, user_vote_ids = self.get_votes_by_user(user_id)
            if code == 200:
                code, tally = self.get_vote_tally(user_vote_ids, normalized=normalized)
                if code == 200:
                    return 200, tally
            return code, None
        except:
            return 500, None
    
    """
    END CALCULATION FUNCTIONS
    """

    """
    Params: Vote ID (int) to modify, influence value (numpy.float64) to assign.
    Returns: 200, vote ID (from the params) if adjustment was successful.
        or   500, None if something went wrong.
    """
    def put_influence(self, vote_id, influence):
        try:
            code, vote = self.get_by_id(vote_id)
            if code == 200:
                vote.influence = influence
                self.votes[vote_id] = vote
                return 200, vote_id
            return code, None
        except:
            return 500, None

    """
    Can only be called after cross-validated predictions have been made and 
    predictions.put_influence() has been called on that corpus.
    
    Params: Instance ID (int) to look up influence for.
    Returns: 200, influence value (numpy.float64) 
        or   404, None if that vote ID does not exist, 
                  or influence has not been calculated yet.
        or   500, None if something went wrong.
    """
    def get_influence(self, vote_id):
        try:
            influence = -1
            if vote_id in self.votes.keys():
                influence = self.votes[vote_id].influence
            if influence != -1:
                return 200, influence
            else:
                return 404, None
        except:
            return 500, None
    
    def put_success(self, vote_id, success):
        try:
            code, vote = self.get_by_id(vote_id)
            if code == 200:
                vote.success = success
                self.votes[vote_id] = vote
                return 200, vote_id
            return code, None
        except:
            return 500, None

    def get_success(self, vote_id):
        try:
            success = None
            if vote_id in self.votes.keys():
                success = self.votes[vote_id].success
            if success is not None:
                return 200, success
            else:
                return 404, None
        except:
            return 500, None

    def get_citations(self, vote_id):
        try:
            editable_citations = None
            if vote_id in self.votes.keys():
                editable_citations = self.votes[vote_id].citations
            if editable_citations is not None:
                return 200, editable_citations
            else:
                return 404, None
        except:
            return 500, None

    def put_citations(self, vote_id, citations):
        try:
            editable_citations = None
            if vote_id in self.votes.keys():
                editable_citations = self.votes[vote_id].citations
                editable_citations.extend(citations)
                self.votes[vote_id].citations = editable_citations
            if editable_citations is not None:
                return 200, editable_citations
            else:
                return 404, None
        except:
            return 500, None

    def put_tenure(self, contrib_id, tenure):
        try:
            code, vote = self.get_by_id(contrib_id)
            if code == 200:
                vote.tenure = tenure
                self.votes[contrib_id] = vote
                return 200, contrib_id
            return code, None
        except:
            return 500, None

    def get_tenure(self, contrib_id):
        try:
            tenure = None
            if contrib_id in self.votes.keys():
                tenure = self.votes[contrib_id].tenure
            if tenure is not None:
                return 200, tenure
            else:
                return 404, None
        except:
            return 500, None


# End VoteEndpoint

class Vote:

    def __init__(self, vote_json):
        self.id            = -1
        self.parent_id     = -1
        self.user_id       = -1
        self.discussion_id = -1
        self.timestamp     = -1
        self.label         = ""
        self.raw_label     = ""
        self.normalized_label = ""
        self.rationale     = ""
        self.influence     = -1
        self.success       = False
        self.citations = []
        self.tenure = -1

        if "ID" in vote_json.keys():
            self.id = vote_json["ID"]
        if "Parent" in vote_json.keys():
            self.parent_id = vote_json["Parent"]
        if "Timestamp" in vote_json.keys():
            self.timestamp = vote_json["Timestamp"]
        if "User" in vote_json.keys():
            self.user_id = vote_json["User"]
        if "Discussion" in vote_json.keys():
            self.discussion_id = vote_json["Discussion"]
        if "Label" in vote_json.keys():
            self.label = vote_json["Label"]
            minimal_label = "Other"
            if "merge" in self.label or "move" in self.label or "userfy" in self.label or "transwiki" in self.label or "incubate" in vote_json["Raw"]:
                minimal_label = "Merge"
            if "redirect" in self.label:
                minimal_label = "Redirect"
            if "keep" in self.label:
                minimal_label = "Keep"
            if "delete" in self.label:
                minimal_label = "Delete"
            if minimal_label == "Other" and ( "withdraw" in self.label or "close" in self.label or "closing" in vote_json["Raw"] or "cancel" in vote_json["Raw"]):
                minimal_label = "Keep"
            if minimal_label == "Other" and ("speedy" in self.label or "copyvio" in vote_json["Raw"] or "csd" in vote_json["Raw"]):
                minimal_label = "Delete"
            self.normalized_label = minimal_label
        if "Raw" in vote_json.keys():
            self.raw_label = vote_json["Raw"]
        if "Rationale" in vote_json.keys():
            self.rationale = vote_json["Rationale"]
            subbed = re.sub("\'\'\'[^\']+\'\'\'", "VOTE", self.rationale)
            self.rationale = subbed
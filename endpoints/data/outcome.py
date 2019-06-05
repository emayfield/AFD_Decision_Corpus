
class OutcomeEndpoint():

    def __init__(self):
        self.outcomes = {}

    """
    Params: JSON representation of an outcome
    Returns: 201, outcome ID of the created JSON
        or   500, None if something went wrong.
    """
    def post_outcome(self, outcome_json):
        outcome = Outcome(outcome_json)
        try:
            outcome_id = outcome.id
            self.outcomes[outcome_id] = outcome
            return 201, outcome_id
        except:
            return 500, None

    """
    Params: None
    Returns: 200, All outcome IDs in this corpus
        or   500, None if something went wrong.
    """
    def get_all(self):
        try:
            return 200, self.outcomes.keys()
        except:
            return 500, None

    """
    Params: ID (int) of a particular outcome to look up
    (note: NOT the discussion ID. Use get_by_discussion_id for that)
    Returns: 200, One single Outcome object if found
        or   404, None if outcome ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_by_id(self, outcome_id):
        try:
            if outcome_id in self.outcomes.keys():
                return 200, self.outcomes[outcome_id]
            else:
                return 404, None
        except:
            return 500, None
        
    """
    Params: ID (int) of a particular outcome to look up
    normalized: int where value corresponds to level of preprocessing.
        0: raw text as originally written.
        1: subset of 13 common terms including keep and delete as well as obscure terms like userfy.
        2: normalized down to 5 possible labels [Keep, Delete, Merge, Redirect, Other]
        3: normalized down to 2 possible labels [Keep, Delete]
    Returns: 200, normalized outcome label if found
        or   404, None if outcome ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_label(self, outcome_id, normalized=3):
        try:
            if normalized == 3:
                norm_label = self.outcomes[outcome_id].normalized_label
                if norm_label == "Merge" or norm_label == "Redirect":
                    norm_label = "Delete"
                if norm_label == "Other":
                    norm_label = "Keep"
                return 200, norm_label
            if normalized == 2:
                return 200, self.outcomes[outcome_id].normalized_label
            elif normalized == 1:
                return 200, self.outcomes[outcome_id].label
            elif normalized == 0:
                return 200, self.outcomes[outcome_id].raw_label
        except KeyError:
            return 404, None
        except:
            return 500, None
      
    """
    Params: ID (int) of a particular outcome to look up
    Returns: 200, rationale text (string) if found
        or   404, None if outcome ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_rationale(self, outcome_id):
        try:
            if outcome_id in self.outcomes.keys():
                return 200, self.outcomes[outcome_id].rationale
            else:
                return 404, None
        except:
            return 500, None
    
    """
    Params: ID (int) of a particular outcome to look up
    Returns: 200, user ID (int) if found
        or   404, None if outcome ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_user_id(self, outcome_id):
        try:
            if outcome_id in self.outcomes.keys():
                return 200, self.outcomes[outcome_id].user_id
            else:
                return 404, None
        except:
            return 500, None


    """
    Params: ID (int) of a particular outcome to look up
    Returns: 200, discussion ID (int) if found
        or   404, None if outcome ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_discussion_id(self, outcome_id):
        try:
            return 200, self.outcomes[outcome_id].discussion_id
        except KeyError:
            return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a particular outcome to look up
    Returns: 200, timestamp since epoch (int) if found
        or   404, None if outcome ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_timestamp(self, outcome_id):
        try:
            if outcome_id in self.outcomes.keys():
                return 200, self.outcomes[outcome_id].timestamp
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: A single user ID (int)
    Returns: 200, All known outcome IDs decided by a single user (presumably an admin). (list)
        or   500, None if something went wrong.
    """
    def get_outcomes_by_user(self, user_id):
        try:
            user_outcome_ids = list(filter(lambda x: self.outcomes[x].user_id == user_id, self.outcomes.keys()))
            return 200, user_outcome_ids
        except:
            return 500, None

    """
    Params: List of outcome_ids to count up
    Returns: 200, dict from label to count
        or   500, None if something else went wrong.

    TODO - should this even be an endpoint here? seems more like analysis.
    """
    def get_outcome_tally(self, outcome_ids, normalized=3):
        try:
            tally = {}
            for outcome_id in outcome_ids:
                code, normalized_label = self.get_label(outcome_id, normalized=normalized)
                if normalized_label in tally.keys():
                    tally[normalized_label] = tally[normalized_label] + 1
                else:
                    tally[normalized_label] = 1
            return 200, tally
        except:
            return 500, None


    """
    Params: One User ID
    Returns: Dict of {
        Normalized outcome label : outcome count
    }
    """
    def get_outcome_tally_by_user(self, user_id):
        try:
            code, user_outcome_ids = self.get_outcomes_by_user(user_id)
            if code == 200:
                code, tally = self.get_outcome_tally(user_outcome_ids)
                if code == 200:
                    return 200, tally
            return code, None
        except:
            return 500, None
    
    """
    NOTE: Right now this must be the *beginning* of a chain of filters (it selects from the whole corpus, not a set of IDs passed in)
    Params: List of outcomes; start timestamp; end timestamp
    Returns: Subset of outcomes from input list that occurred between timestamps (inclusive)
    """
    def get_outcomes_by_timestamps(self, start=0, end=2145916800):
        try:
            outcome_ids = list(filter(lambda x: self.outcomes[x].timestamp >= start and self.outcomes[x].timestamp <= end, self.outcomes.keys()))
            return 200, outcome_ids
        except:
            return 500, None

class Outcome:

    def __init__(self, outcome_json):
        self.id = -1
        self.discussion_id = -1
        self.timestamp = -1
        self.user_id = -1
        self.label = ""
        self.raw_label = ""
        self.normalized_label = ""
        self.rationale = ""

        if "ID" in outcome_json.keys():
            self.id = outcome_json["ID"]
        if "Parent" in outcome_json.keys():
            self.discussion_id = outcome_json["Parent"]
        if "Timestamp" in outcome_json.keys():
            self.timestamp = outcome_json["Timestamp"]
        if "User" in outcome_json.keys():
            self.user_id = outcome_json["User"]
        if "Label" in outcome_json.keys():
            self.label = outcome_json["Label"]
            minimal_label = "Other"
            if "merge" in self.label or "move" in self.label or "userfy" in self.label or "transwiki" in self.label or "incubate" in outcome_json["Raw"]:
                minimal_label = "Merge"
            if "redirect" in self.label:
                minimal_label = "Redirect"
            if "keep" in self.label:
                minimal_label = "Keep"
            if "delete" in self.label:
                minimal_label = "Delete"
            if minimal_label == "Other" and ( "withdraw" in self.label or "close" in self.label or "closing" in outcome_json["Raw"] or "cancel" in outcome_json["Raw"]):
                minimal_label = "Keep"
            if minimal_label == "Other" and ("speedy" in self.label or "copyvio" in outcome_json["Raw"] or "csd" in outcome_json["Raw"]):
                minimal_label = "Delete"
            self.normalized_label = minimal_label
        if "Raw" in outcome_json.keys():
            self.raw_label = outcome_json["Raw"]
        if "Rationale" in outcome_json.keys():
            self.rationale = outcome_json["Rationale"]
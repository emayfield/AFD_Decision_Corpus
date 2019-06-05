class NominationEndpoint:

    def __init__(self):
        self.nominations = {}

    """
    Params: JSON representation of a nomination.
    Returns: 201, ID of the created Nomination object.
        or   500, None if something went wrong.
    """
    def post_nomination(self, nomination_json):
        nomination = Nomination(nomination_json)
        try:
            nomination_id = nomination.id
            self.nominations[nomination_id] = nomination
            return 201, nomination_id
        except:
            return 500, None

    """
    Params: none
    Returns: 200, All known nomination IDs (list) in the corpus
        or   500, None if something went wrong.
    """
    def get_all(self):
        try:
            return 200, self.nominations.keys()
        except:
            return 500, None

    """
    Params: ID (int) of a particular nomination to look up
    (note: NOT the discussion ID. Use get_by_discussion_id for that)
    Returns: 200, One single nomination object if found
        or   404, None if nomination ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_by_id(self, nomination_id):
        try:
            if nomination_id in self.nominations.keys():
                return 200, self.nominations[nomination_id]
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a particular nomination to look up
    Returns: 200, nomination text (string) if found
        or   404, None if nomination ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_text(self, nomination_id):
        try:
            if nomination_id in self.nominations.keys():
                return 200, self.nominations[nomination_id].text
            else:
                return 404, None
        except:
            return 500, None
    
    """
    Params: ID (int) of a particular nomination to look up
    Returns: 200, user_id (int) if that nomination has a user_id
        or   404, None if nomination ID does not exist.
        or   500, None if something went wrong.
    """
    def get_user_id(self, nomination_id):
        try:
            if nomination_id in self.nominations.keys():
                return 200, self.nominations[nomination_id].user_id
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a particular nomination to look up
    Returns: 200, timestamp since epoch (int) if found
        or   404, None if nomination ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_timestamp(self, nomination_id):
        try:
            if nomination_id in self.nominations.keys():
                return 200, self.nominations[nomination_id].timestamp
            else:
                return 404, None
        except:
            return 500, None
    
    """
    Params: ID (int) of a particular nomination to look up
    Returns: 200, discussion ID (int) if found
        or   404, None if nomination ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_discussion_id(self, nomination_id):
        try:
            if nomination_id in self.nominations.keys():
                return 200, self.nominations[nomination_id].discussion_id
            else:
                return 404, None
        except:
            return 500, None


    """
    Params: A single discussion ID (int)
    Returns: 200, Nomination ID for a single discussion (if one exists). (int)
        or   500, None if something went wrong.
    """
    def get_nomination_by_discussion(self, disc_id):
        try:
            discussion_nomination_id = list(filter(lambda x: self.nominations[x].discussion_id == disc_id, self.nominations.keys()))[0]
            return 200, discussion_nomination_id
        except:
            return 500, None

    
    def get_citations(self, nom_id):
        try:
            editable_citations = None
            if nom_id in self.nominations.keys():
                editable_citations = self.nominations[nom_id].citations
            if editable_citations is not None:
                return 200, editable_citations
            else:
                return 404, None
        except:
            return 500, None

    def put_citations(self, nom_id, citations):
        try:
            editable_citations = None
            if nom_id in self.nominations.keys():
                editable_citations = self.nominations[nom_id].citations
                editable_citations.extend(citations)
                self.nominations[nom_id].citations = editable_citations
            if editable_citations is not None:
                return 200, editable_citations
            else:
                return 404, None
        except:
            return 500, None

    def put_tenure(self, contrib_id, tenure):
        try:
            code, nom = self.get_by_id(contrib_id)
            if code == 200:
                nom.tenure = tenure
                self.nominations[contrib_id] = nom
                return 200, contrib_id
            return code, None
        except:
            return 500, None

    def get_tenure(self, contrib_id):
        try:
            tenure = None
            if contrib_id in self.nominations.keys():
                tenure = self.nominations[contrib_id].tenure
            if tenure is not None:
                return 200, tenure
            else:
                return 404, None
        except:
            return 500, None

class Nomination:
    def __init__(self, nomination_json):
        self.id            = -1
        self.parent_id     = -1
        self.user_id       = -1
        self.discussion_id = -1
        self.timestamp     = -1
        self.text          = ""
        self.citations = []
        self.tenure = -1

        if "ID" in nomination_json.keys():
            self.id = nomination_json["ID"]
        if "Parent" in nomination_json.keys():
            self.parent_id = nomination_json["Parent"]
        if "Timestamp" in nomination_json.keys():
            self.timestamp = nomination_json["Timestamp"]
        if "User" in nomination_json.keys():
            self.user_id = nomination_json["User"]
        if "Discussion" in nomination_json.keys():
            self.discussion_id = nomination_json["Discussion"]
        if "Text" in nomination_json.keys():
            self.text = nomination_json["Text"]
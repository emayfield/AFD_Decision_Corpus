class CitationEndpoint:

    def __init__(self):
        self.citations = {}

    """
    Params: JSON representation of a citation.
    Returns: 201, ID of the created citation object.
        or   500, None if something went wrong.
    """
    def post_citation(self, citation_json):
        citation = Citation(citation_json)
        try:
            citation_id = citation.id
            self.citations[citation_id] = citation
            return 201, citation_id
        except:
            return 500, None

    """
    Params: none
    Returns: 200, All known citation IDs (list) in the corpus
        or   500, None if something went wrong.
    """
    def get_all(self):
        try:
            return 200, self.citations.keys()
        except:
            return 500, None

    """
    Params: ID (int) of a particular citation to look up
    (note: NOT the discussion ID. Use get_by_discussion_id for that)
    Returns: 200, One single citation object if found
        or   404, None if citation ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_by_id(self, citation_id):
        try:
            if citation_id in self.citations.keys():
                return 200, self.citations[citation_id]
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a particular citation to look up
    Returns: 200, citation text (string) if found
        or   404, None if citation ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_text(self, citation_id):
        try:
            if citation_id in self.citations.keys():
                return 200, self.citations[citation_id].text
            else:
                return 404, None
        except:
            return 500, None

class Citation:
    def __init__(self, citation_json):
        self.id            = -1
        self.parent_id     = -1
        self.policy        = ""

        if "ID" in citation_json.keys():
            self.id = citation_json["ID"]
        if "Parent" in citation_json.keys():
            self.parent_id = citation_json["Parent"]
        if "Text" in citation_json.keys():
            self.text = citation_json["Text"]
class CommentEndpoint:

    def __init__(self):
        self.comments = {}

    """
    Params: JSON representation of a comment.
    Returns: 201, ID of the created Comment object.
        or   500, None if something went wrong.
    """
    def post_comment(self, comment_json):
        comment = Comment(comment_json)
        try:
            comment_id = comment.id
            self.comments[comment_id] = comment
            return 201, comment_id
        except:
            return 500, None

    """
    Params: none
    Returns: 200, All known Comment IDs (list) in the corpus
        or   500, None if something went wrong.
    """
    def get_all(self):
        try:
            return 200, self.comments.keys()
        except:
            return 500, None

    """
    Params: ID (int) of a particular comment to look up
    (note: NOT the discussion ID. Use get_by_discussion_id for that)
    Returns: 200, One single Comment object if found
        or   404, None if comment ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_by_id(self, comment_id):
        try:
            if comment_id in self.comments.keys():
                return 200, self.comments[comment_id]
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a particular comment to look up
    Returns: 200, comment text (string) if found
        or   404, None if comment ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_text(self, comment_id):
        try:
            if comment_id in self.comments.keys():
                return 200, self.comments[comment_id].text
            else:
                return 404, None
        except:
            return 500, None
    
    """
    Params: ID (int) of a particular comment to look up
    Returns: 200, user_id (int) if that comment has a user_id
        or   404, None if comment ID does not exist.
        or   500, None if something went wrong.
    """
    def get_user_id(self, comment_id):
        try:
            if comment_id in self.comments.keys():
                return 200, self.comments[comment_id].user_id
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a particular comment to look up
    Returns: 200, timestamp since epoch (int) if found
        or   404, None if comment ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_timestamp(self, comment_id):
        try:
            if comment_id in self.comments.keys():
                return 200, self.comments[comment_id].timestamp
            else:
                return 404, None
        except:
            return 500, None
    
    """
    Params: ID (int) of a particular comment to look up
    Returns: 200, discussion ID (int) if found
        or   404, None if comment ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_discussion_id(self, comment_id):
        try:
            if comment_id in self.comments.keys():
                return 200, self.comments[comment_id].discussion_id
            else:
                return 404, None
        except:
            return 500, None


    """
    Params: A single discussion ID (int)
    Returns: 200, All known comment IDs in a single discussion. (list)
        or   500, None if something went wrong.
    """
    def get_comments_by_discussion(self, disc_id):
        try:
            discussion_comment_ids = list(filter(lambda x: self.comments[x].discussion_id == disc_id, self.comments.keys()))
            return 200, discussion_comment_ids
        except:
            return 500, None

    """
    NOTE: Right now this must be the *beginning* of a chain of filters (it selects from the whole corpus, not a set of IDs passed in)
    Params: start timestamp; end timestamp
    Returns: 200, Subset of comments that occurred between timestamps (inclusive)
        or   500, None if something else went wrong.
    """
    def get_comments_by_timestamps(self, start=0, end=2145916800):
        try:
            print(len(self.comments))
            comment_ids = list(filter(lambda x: start <= self.comments[x].timestamp <= end, self.comments.keys()))
            return 200, comment_ids
        except:
            return 500, None


    """
    Params: Comment ID (int) to modify, influence value (numpy.float64) to assign.
    Returns: 200, comment ID (from the params) if adjustment was successful.
        or   500, None if something went wrong.
    """
    def put_influence(self, comment_id, influence):
        try:
            code, comment = self.get_by_id(comment_id)
            if code == 200:
                comment.influence = influence
                self.comments[comment_id] = comment
                return 200, comment_id
            return code, None
        except:
            return 500, None


    """
    Can only be called after cross-validated predictions have been made and 
    predictions.put_influence() has been called on that corpus.
    
    Params: Comment ID (int) to look up influence for.
    Returns: 200, influence value (numpy.float64) 
        or   404, None if that comment ID does not exist, 
                  or influence has not been calculated yet.
        or   500, None if something went wrong.
    """
    def get_influence(self, comment_id):
        try:
            influence = -1
            if comment_id in self.comments.keys():
                influence = self.comments[comment_id].influence
            if influence != -1:
                return 200, influence
            else:
                return 404, None
        except:
            return 500, None


    def get_citations(self, comment_id):
        try:
            editable_citations = None
            if comment_id in self.comments.keys():
                editable_citations = self.comments[comment_id].citations
            if editable_citations is not None:
                return 200, editable_citations
            else:
                return 404, None
        except:
            return 500, None

    def put_citations(self, comment_id, citations):
        try:
            editable_citations = None
            if comment_id in self.comments.keys():
                editable_citations = self.comments[comment_id].citations
                editable_citations.extend(citations)
                self.comments[comment_id].citations = editable_citations
            if editable_citations is not None:
                return 200, editable_citations
            else:
                return 404, None
        except:
            return 500, None

    def put_tenure(self, contrib_id, tenure):
        try:
            code, comment = self.get_by_id(contrib_id)
            if code == 200:
                comment.tenure = tenure
                self.comments[contrib_id] = comment
                return 200, contrib_id
            return code, None
        except:
            return 500, None

    def get_tenure(self, contrib_id):
        try:
            tenure = None
            if contrib_id in self.comments.keys():
                tenure = self.comments[contrib_id].tenure
            if tenure is not None:
                return 200, tenure
            else:
                return 404, None
        except:
            return 500, None

class Comment:
    def __init__(self, comment_json):
        self.id            = -1
        self.parent_id     = -1
        self.user_id       = -1
        self.discussion_id = -1
        self.timestamp     = -1
        self.text          = ""
        self.influence     = -1
        self.citations = []
        self.tenure = -1

        if "ID" in comment_json.keys():
            self.id = comment_json["ID"]
        if "Parent" in comment_json.keys():
            self.parent_id = comment_json["Parent"]
        if "Timestamp" in comment_json.keys():
            self.timestamp = comment_json["Timestamp"]
        if "User" in comment_json.keys():
            self.user_id = comment_json["User"]
        if "Discussion" in comment_json.keys():
            self.discussion_id = comment_json["Discussion"]
        if "Text" in comment_json.keys():
            self.text = comment_json["Text"]
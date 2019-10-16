import numpy as np

class VectorEndpoint:
    def __init__(self, server):
        self.server = server
        self.vectors = {}

    def get_override(self, vector_id):
        code, vector = self.get_by_id(vector_id)
        if code == 200:
            return code, vector.override_y
        else:
            return code, False

    def post_extract_comment_features(self, instance_id, target_id, vote_timestamp):
        try:
            x = {}

            code, override_y = self.server.votes.get_label(target_id, normalized=self.server.config["normalized"])
            for endpoint in self.server.extractors:
                code, features = endpoint.extract_features(instance_id, vote_timestamp, contrib_ids=[target_id])
                x.update(features)
            vector = Vector(instance_id, target_id, x, override_y=override_y)
            vector_id = vector.id
            self.vectors[vector_id] = vector

            self.server.instances.put_vector_id(instance_id, vector_id)
            return 201, vector_id
        except Exception as e:
            print(e)
            return 500, None
        

    """
    Params: Instance ID to extract features from at time vote_timestamp (int)
    Returns: 201, vector ID of extracted features from all extractors on the server.
        or   500, None if something went wrong.
    """
    def post_extract_features(self, instance_id, target_id, vote_timestamp):        
        try:
            x = {}
            for endpoint in self.server.extractors:
                code, features = endpoint.extract_features(instance_id, vote_timestamp)
                x.update(features)
            vector = Vector(instance_id, target_id, x)
            vector_id = vector.id
            self.vectors[vector_id] = vector
            self.server.instances.put_vector_id(instance_id, vector_id)
            return 201, vector_id
        except Exception as e:
            return 500, None

    """
    Params: None
    Returns: 200, concatenated list of feature names for all extractors on the server.
    """
    def get_feature_names(self):
        names = []
        for endpoint in self.server.extractors:
            code, feature_names = endpoint.feature_names()
            if feature_names is not None:
                names.extend(feature_names)
        return 200, names

        
    """
    Params: none
    Returns: 200, All known Vector IDs (list) in the corpus
        or   500, None if something went wrong.
    """
    def get_all(self):
        try:
            return 200, self.vectors.keys()
        except:
            return 500, None

    """
    Params: ID (int) of a particular vector ID to look up
    Returns: 200, One single Vector object if found
        or   404, None if ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_by_id(self, vector_id):
        try:
            if vector_id in self.vectors.keys():
                return 200, self.vectors[vector_id]
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID of a vector to look up.
    Returns: 200, underlying instance ID that this vector's features were extracted from.
        or   404, None if this vector ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_instance_id(self, vector_id):
        try:
            if vector_id in self.vectors.keys():
                return 200, self.vectors[vector_id].instance_id
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID of a vector to look up.
    Returns: 200, feature name->values (dict) of extracted features for that ID.
        or   404, None if this vector ID does not exist.
        or   500, None if something went wrong.
    """
    def get_x(self, vector_id):
        try:
            if vector_id in self.vectors.keys():
                return 200, self.vectors[vector_id].x
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: Instance ID to generate comment vectors for.
            Skip_comments: Whether to generate instances for comments+votes or just votes 
                           (default: just votes)
            Skip_empty: Whether to generate instances for 'incomplete' discussions without 
                        at least one nominating statement, vote, and outcome.
                        (default: yes, skip those conversations)
    Returns: 201, vector IDs (list) created within this call.
        or   5

    """
    def post_comment_task_x(self, instance_id, skip_comments=True):
        try:
            vector_ids = []
            code, original_contrib_ids = self.server.instances.get_contribution_ids(instance_id)

            skip_empty = self.server.config["strict_discussions"]
            if skip_empty:
                has_vote = False
                has_nom = False
                has_out = False
                for orig_id in original_contrib_ids:
                    is_vote = self.server.util.is_vote(orig_id)
                    is_nom = self.server.util.is_nomination(orig_id)
                    is_outcome = self.server.util.is_outcome(orig_id)
                    if is_vote:
                        has_vote = True
                    if is_nom:
                        has_nom = True
                    if is_outcome:
                        has_out = True
                if not (has_vote and has_nom and has_out):
                    return 201, vector_ids

            for orig_id in original_contrib_ids:
                is_vote = self.server.util.is_vote(orig_id)
                contrib_timestamp = -1
                if is_vote or not skip_comments:
                    code, contrib_timestamp = self.server.votes.get_timestamp(orig_id)
                if contrib_timestamp != -1:
                    code, vector_id = self.post_extract_comment_features(instance_id, orig_id, contrib_timestamp)
                    if code == 201:
                        self.put_is_full_discussion(vector_id, True)
                        vector_ids.append(vector_id)
            return 201, vector_ids
        except Exception as e:
            print(e)
            return 500, None

    """
    Params: An instance ID from a corpus.
            Multiply: Bool, if false, create one vector for each instance.
            If true, create a vector for the moment before *each* vote in 
            the discussion represented by an instance.
    Returns: 201, vector IDs (list) created within this call.
        or   500, None if something went wrong.
    """
    def post_all_x(self, instance_id, multiply=False):
        try:
            vector_ids = []
            code, original_contrib_ids = self.server.instances.get_contribution_ids(instance_id)
            code, discussion_id = self.server.instances.get_discussion_id(instance_id)

            skip_empty = self.server.config["strict_discussions"]
            if skip_empty:
                has_vote = False
                has_nom = False
                has_out = False
                for orig_id in original_contrib_ids:
                    is_vote = self.server.util.is_vote(orig_id)
                    is_nom = self.server.util.is_nomination(orig_id)
                    is_outcome = self.server.util.is_outcome(orig_id)
                    if is_vote:
                        has_vote = True
                    if is_nom:
                        has_nom = True
                    if is_outcome:
                        has_out = True
                if not (has_vote and has_nom and has_out):
                    print("This is an empty discussion: {} {} {}".format(discussion_id, has_vote, has_out))
                    return 201, vector_ids

            if multiply:
                """
                Create a vector for every vote as a "moment in time" to try to predict the future.
                """
                for orig_id in original_contrib_ids:
                    orig_code = str(orig_id)[0]
                    contrib_timestamp = -1
                    if orig_code == "4":
                        code, contrib_timestamp = self.server.votes.get_timestamp(orig_id)
                    if orig_code == "5":
                        code, contrib_timestamp = self.server.comments.get_timestamp(orig_id)
                    if contrib_timestamp != -1:
                        code, vector_id = self.post_extract_features(instance_id, orig_id, contrib_timestamp)
                        if code == 201:
                            vector_ids.append(vector_id)
                    

            code, vector_id = self.post_extract_features(instance_id, instance_id, 999999999999)
            if code == 201:
                self.put_is_full_discussion(vector_id, True)
                vector_ids.append(vector_id)
            return 201, vector_ids
        except Exception as e:
            print(e)
            return 500, None

    """
    Params: Vector ID to look up
    Returns: 200, bool: True if this vector includes all features from the whole discussion (extraction timestamp > last contribution timestamp)
                    or  False if extraction timestamp was less than at least one contribution timestamp.
        or   404, None if that vector ID does not exist.
        or   500, None if something went wrong.
    """
    def get_is_full_discussion(self, vector_id):
        try:
            if vector_id in self.vectors.keys():
                return 200, self.vectors[vector_id].full_discussion
            else:
                return 404, None
        except:
            return 500, None

    """
    """
    def put_is_full_discussion(self, vector_id, full_bool):
        try:
            if vector_id in self.vectors.keys():
                code, vector = self.get_by_id(vector_id)
                vector.full_discussion = full_bool
                self.vectors[vector_id] = vector
                return 200, vector_id
            else:
                return 404, None
        except:
            return 500, None

    """
    """
    def get_target_id(self, vector_id):
        try:
            if vector_id in self.vectors.keys():
                return 200, self.vectors[vector_id].target_id
            else:
                return 404, None
        except:
            return 500, None
    

class Vector:

    global_id = 1
    def __init__(self, instance_id, target_id, x, override_y=None):
        self.instance_id = instance_id
        self.target_id = target_id
        self.x = x
        self.id = -(200000000 + Vector.global_id)
        self.full_discussion = False
        self.override_y = override_y


        Vector.global_id += 1
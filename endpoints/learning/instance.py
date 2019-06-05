import numpy as np

class InstanceEndpoint:

    def __init__(self, server):
        self.server = server
        self.instances = {}

    """
    Params: Discussion ID, timestamp of moment to make prediction (capture all events before that time as input)
    Returns: 201, Instance ID if instance was successfully created.
        or   500, None if something went wrong.
    """
    def post_instance(self, disc_id, timestamp):
        try:
            code, input_contributions = self.server.discussions.get_contributions_at_time(disc_id, timestamp)
            code, outcome_id = self.server.discussions.get_outcome_id(disc_id)
            code, outcome_label = self.server.outcomes.get_label(outcome_id, normalized=self.server.config["normalized"])
            instance = Instance(disc_id, input_contributions, outcome_label)
            instance_id = instance.id
            self.instances[instance_id] = instance
            return 201, instance_id
        except:
            return 500, None

    """
    Params: none
    Returns: 200, All known Instance IDs (list) in the corpus
        or   500, None if something went wrong.
    """
    def get_all(self):
        try:
            return 200, self.instances.keys()
        except:
            return 500, None

    """
    Params: ID (int) of a particular instance ID to look up
    Returns: 200, One single Instance object if found
        or   404, None if ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_by_id(self, instance_id):
        try:
            if instance_id in self.instances.keys():
                return 200, self.instances[instance_id]
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: instance id (int) to look up
    Returns: 200, all contribution IDs (list) from this instance 
                  (prior to the timestamp the instance was generated for)
        or   404, None if that instance ID does not exist.
        or   500, None if something went wrong.
    """
    def get_contribution_ids(self, instance_id):
        try:
            if instance_id in self.instances.keys():
                return 200, self.instances[instance_id].contributions
            else:
                return 404, None
        except:
            return 500, None


    """
    Params: instance ID (int) to look up
    Returns: 200, discussion ID that this instance was drawn from.
        or   404, None if this ID does not exist.
        or   500, None if something went wrong.
    """
    def get_discussion_id(self, instance_id):
        try:
            if instance_id in self.instances.keys():
                return 200, self.instances[instance_id].discussion_id
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: Instance ID (int) to look up
    Returns: 200, the Y value (str) for this instance for training purposes
             (corresponds to the outcome label from the underlying discussion)
        or   404, None if this instance ID does not exist.
        or   500, None if something went wrong.
    """
    def get_y(self, instance_id):
        try:
            if instance_id in self.instances.keys():
                return 200, self.instances[instance_id].Y
            else:
                return 404, None
        except:
            return 500, None

    """
    We have created a new vector in the dataset based on this instance
    and want to keep track of all the vectors that were spawned from that discussion,
    all in one place for easy access.

    Params: Instance ID to add a vector ID to,
            Vector ID to add to that instance
    Returns: 200, that same vector ID if the insert was successful.
        or   404, None if that instance ID does not exist.
        or   500, None if something went wrong.
    """
    def put_vector_id(self,instance_id,vector_id):
        try:
            if instance_id in self.instances.keys():
                self.instances[instance_id].vector_ids.append(vector_id)
                return 200, vector_id
            else:
                return 404, None
        except:
            return 500, None
        
    """
    All the vectors that have been generated based on data from this instance.
    Params: Instance ID to look up (int)
    Returns: 200, Vector IDs (list) based on this instance.
        or   404, None if that instance ID does not exist.
        or   500, None if something went wrong.
    """
    def get_vector_ids(self, instance_id):
        try:
            if instance_id in self.instances.keys():
                return 200, self.instances[instance_id].vector_ids
            else:
                return 404, None
        except Exception as e:
            return 500, None


class Instance:

    global_id = 1
    def __init__(self, discussion_id, contrib_ids, y):
        self.discussion_id = discussion_id
        self.contributions = contrib_ids
        self.vector_ids = []
        self.Y = y
        self.id = -(100000000 + Instance.global_id)
        Instance.global_id += 1

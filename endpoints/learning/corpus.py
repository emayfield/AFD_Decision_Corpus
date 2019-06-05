import numpy as np

class CorpusEndpoint:
    def __init__(self, server):
        self.server = server
        self.corpora = {}

    """
    Params: Set of Vector ids in combined train+test set
    Return 201, A Corpus object containing all the feature vectors passed in.
            EXCEPT vectors with a None label are tossed out.
        or 500, None if something went wrong.
    """
    def post_corpus(self, vector_ids):
        try:
            screened_vectors = []
            code, feature_names = self.server.vectors.get_feature_names()
            dropped = 0
            for vector_id in vector_ids:
                code, instance_id = self.server.vectors.get_instance_id(vector_id)
                code, y = self.server.instances.get_y(instance_id)
                if y is not None:
                    screened_vectors.append(vector_id)
                else:
                    dropped += 1
                    print("Dropping {}".format(vector_id))
            corpus = Corpus(feature_names, screened_vectors)
            c_id = corpus.id
            self.corpora[c_id] = corpus
            print("{} total dropped".format(dropped))
            return 201, c_id
        except:
            return 500, None
        

    """
    Params: none
    Returns: 200, All known corpora (list) on the server
        or   500, None if something went wrong.
    """
    def get_all(self):
        try:
            return 200, self.corpora.keys()
        except:
            return 500, None

    """
    Params: ID (int) of a particular corpus to look up
    Returns: 200, One single Corpus object if found
        or   404, None if ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_by_id(self, c_id):
        try:
            if c_id in self.corpora.keys():
                return 200, self.corpora[c_id]
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a corpus to look up
    Returns: 200, set of vector IDs in that corpus.
        or   404, None if that corpus ID does not exist.
        or   500, None if something went wrong.
    """
    def get_vector_ids(self, c_id):
        try:
            if c_id in self.corpora.keys():
                return 200, self.corpora[c_id].vector_ids
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a corpus to look up
    Returns: 200, set of gold labels for each vector ID in the corpus (in order)
        or   500, None if something went wrong.
    """
    def get_y(self, c_id):
        try:
            code, vector_ids = self.get_vector_ids(c_id)
            num_instances = len(vector_ids)
            y_array = []
            for i in range(num_instances):
                vector_id = vector_ids[i]
                code, override = self.server.vectors.get_override(vector_id)
                if not override:
                    code, instance_id = self.server.vectors.get_instance_id(vector_id)
                    code, y = self.server.instances.get_y(instance_id)
                    y_array.append(y)
                else:
                    y_array.append(override)
            return 200, y_array
        except:
            return 500, None

    def get_feature_names(self, c_id):
        try:
            if c_id in self.corpora.keys():
                return 200, self.corpora[c_id].feature_names
            else:
                return 404, None
        except:
            return 500, None


    """
    Params: ID (int) of a corpus to look up
    Returns: Three values!
    200, dict of feature names to indices, 2D numpy array 
    Numpy array represents all instances and features in the corpus.
    Feature name dict lets you look up feature values by feature name
        or   500, None if something went wrong.
    """
    def get_x_numpy(self, c_id):
        try:
            code, vector_ids = self.get_vector_ids(c_id)
            code, names = self.get_feature_names(c_id)
            if code == 200:
                feature_name_dict = {}
                id = 0
                for n in names:
                    feature_name_dict[n] = id
                    id += 1
                print("Finished names, {}.".format(id))
                num_features = id
                num_instances = len(vector_ids)
                total_features = np.zeros((num_instances, num_features), dtype=object)
                for i in range(num_instances):
                    vector_id = vector_ids[i]
                    code, vector_dict = self.server.vectors.get_x(vector_id)

                    # TODO - rewrite as regular python lists then convert to numpy at the end.
                    for f in vector_dict.keys():
                        if f in feature_name_dict.keys():
                            total_features[i,feature_name_dict[f]] = vector_dict[f]
                return 200, feature_name_dict, total_features
            else:
                return 200, {}, np.empty([0,0])
        except Exception as e:
            print("corpus error: {}".format(e))
            return 500, None

class Corpus:
    global_id = 1
    def __init__(self, feature_names, vector_ids):
        self.vector_ids = vector_ids
        self.feature_names = feature_names
        self.id = -(300000000 + Corpus.global_id)
        Corpus.global_id += 1
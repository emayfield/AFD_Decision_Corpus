from sklearn.feature_extraction.text import CountVectorizer
import warnings
import json
from endpoints.helpers.cache import lookup, store

class BOWEndpoint:

    task_path = None
    cache_path = None

    def __init__(self, server):
        self.server = server
        self.names = {}

        BOWEndpoint.cache_path = open("cachepath","r").read().strip()
        BOWEndpoint.task_path = "bow_discussion"
    """
    Returns: 200, feature names (list) for timestamp-related features and vote counts (both % and #).
    Right now just the 10 features of # and % for each of five vote labels is frustratingly effective.
    """
    def feature_names(self):
        out_names = filter(lambda x: self.names[x] > 5, self.names.keys())
        return 200, list(out_names)


    def extract_features(self, instance_id, vote_timestamp, contrib_ids=None):
        code, discussion_id = self.server.instances.get_discussion_id(instance_id)
        if contrib_ids is None:
            code, contrib_ids = self.server.discussions.get_contributions_at_time(discussion_id, vote_timestamp)
        code, (beginning, end) = self.server.discussions.get_timestamp_range(discussion_id)
        if code != 200:
            return code, None

#        print("Contribs: {} ".format(contrib_ids))

        vectorizer = CountVectorizer( 
                        ngram_range=(1,1), 
                        lowercase=True,
                        min_df=1
                        )

        texts = []
        ids = []
        for contrib_id in contrib_ids:
            code, contrib_text = self.server.util.get_text(contrib_id)
            code, contrib_timestamp = self.server.util.get_timestamp(contrib_id)

            if contrib_text is not None and len(contrib_text.split()) > 0:
                texts.append(contrib_text)
                ids.append(contrib_id)

        unigrams = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            unigrams = vectorizer.fit_transform(texts)
        
        x_dict = {}
        if unigrams is not None and vectorizer.vocabulary_ is not None:
            vocab = vectorizer.vocabulary_
            vocab_lookup = {vocab[k]:k for k in vocab.keys()}
            for i in range(len(texts)):
                placeholder, feats = unigrams[i].nonzero()
                for index in feats:
                    feat = vocab_lookup[index]
                    x_dict[feat] = 1
                    if feat not in self.names.keys():
                        self.names[feat] = 1
                    else:
                        self.names[feat] = self.names[feat] + 1
        if(instance_id % 100 == 0):
            print("Embedded: instance {}, {} texts".format(instance_id, len(texts)))
            print("Found {} keys, now {} total ({} filtered)".format(len(x_dict.keys()), len(self.names.keys()), len(self.feature_names()[1])))
        
        if False:
            store(BOWEndpoint.cache_path, BOWEndpoint.task_path, instance_id, json.dumps(x_dict))

        return 201, x_dict
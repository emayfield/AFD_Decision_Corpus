import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
import warnings

import math

"""
Feature extractor for the text representation of all the contributions in a discussion.
Right now, this uses GloVe word embedding to represent unigram features as an N-dimensional array
(current allowed N = 50, 100, 200, 300). With a 50-dimensional embedding space and 20k training instances,
performance goes up by about 0.2% raw and 0.005 K relative to vote tallies alone. 

TODO:
- Test performance benefit of higher dimensions
- Test performance benefit of more training data.
- Test performance benefit of using Diyi's WP-specific embedding instead of GloVe
- Test performance using only subsets of votes / comments / nominations, all three
- Test performance by weighting or separating those feature spaces into multiple dimensions.
"""
class EmbeddingEndpoint:
    
    glove = None

    def __init__(self, server):
        self.server = server
        self.dimensions = 300
        self.vectors = {}

        print("Loading glove model")
        if EmbeddingEndpoint.glove is None:
            gloveFile = "glove.6B/glove.6B.{}d.txt".format(self.dimensions)
            f = open(gloveFile,'r')
            model = {}
            i = 0
            for line in f:
                splitLine = line.split()
                word = splitLine[0]
                embedding = np.array([float(val) for val in splitLine[1:]])
                model[word] = embedding
                i += 1
                if i % 10000 == 0:
                    print("{} words from disk".format(i))
            print("Done! {} words loaded!".format(len(model.keys())))
            EmbeddingEndpoint.glove = model
        else:
            print("No need to load")

    """
    Params: None
    Returns: 200, List of feature names for the embedding space (meaningless "D1...D50")
    """
    def feature_names(self):
        return 200, ["D{}".format(i) for i in range(self.dimensions)]


    """
    Params: Instance ID for a single discussion and timestamp to extract features from.
    Returns: 200, Word embedding space representation of the full conversation up to that point.
    Each appearance of a word is added to the vector once, regardless of location; the vector 
    is normalized by total word count of the discussion.

    Format: (dict) feature name (str) to value (float64)

    Currently, all of votes, comments, and nominations are included in the representation.
    """
    def extract_features(self, instance_id, vote_timestamp, contrib_ids=None):
        try:
            code, discussion_id = self.server.instances.get_discussion_id(instance_id)
            if contrib_ids is None:
                code, contrib_ids = self.server.discussions.get_contributions_at_time(discussion_id, vote_timestamp)
            code, (beginning, end) = self.server.discussions.get_timestamp_range(discussion_id)
            if code != 200:
                return code, None

            vectorizer = CountVectorizer( 
                            ngram_range=(1,1), 
                            lowercase=True,
                            min_df=1
                            )

            total_features = None
            texts = []
            text_logs = []
            for contrib_id in contrib_ids:
                code, contrib_text = self.server.util.get_text(contrib_id)

                if contrib_text is not None and len(contrib_text.split()) > 0:
                    texts.append(contrib_text)
                    log_tokens = math.log(len(contrib_text.split()))
                    text_logs.append(log_tokens)

            unigrams = None
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                unigrams = vectorizer.fit_transform(texts)
            
            sum_embedding = np.zeros(self.dimensions)
            if unigrams is not None and vectorizer.vocabulary_ is not None:
                vocab = vectorizer.vocabulary_
                vocab_lookup = {vocab[k]:k for k in vocab.keys()}
                total_embeddings = 0
                for i in range(len(texts)):
                    placeholder, feats = unigrams[i].nonzero()
                    this_embedding = np.zeros(self.dimensions)
                    feat_embeddings = 0
                    for feat in feats:
                        index = vocab_lookup[feat]
                        if index in EmbeddingEndpoint.glove.keys():
                            embedding = EmbeddingEndpoint.glove[index]
                            frequency = unigrams[i,feat]
                            feat_embeddings += frequency
                            embedding = np.multiply(embedding, frequency)
                            this_embedding = np.add(this_embedding, embedding)
                    if feat_embeddings > 0 and text_logs[i] != 0:
                        this_embedding = np.divide(this_embedding, text_logs[i])
                        sum_embedding = np.add(sum_embedding, this_embedding)
                        total_embeddings += 1
                if total_embeddings > 0:
                    sum_embedding = np.divide(sum_embedding, total_embeddings)
            if(instance_id % 100 == 0):
                print("Embedded: instance {}, {} dimensions, {} texts".format(instance_id, len(sum_embedding), len(texts)))

            x = list(np.array(sum_embedding))
            x_dict = {"D{}".format(i):x[i] for i in range(len(x))}
            return 201, x_dict
        except Exception as e:
            print(e)
            return 500, None
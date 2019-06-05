import json
import time
import os
import csv
from endpoints.data.discussion import DiscussionEndpoint
from endpoints.data.user       import UserEndpoint
from endpoints.data.outcome    import OutcomeEndpoint
from endpoints.data.vote       import VoteEndpoint
from endpoints.data.comment    import CommentEndpoint
from endpoints.data.nomination import NominationEndpoint
from endpoints.helpers.utilities import UtilitiesEndpoint
from endpoints.helpers.math      import MathEndpoint
from endpoints.helpers.analysis  import AnalysisEndpoint
from endpoints.learning.instance   import InstanceEndpoint
from endpoints.learning.vector     import VectorEndpoint
from endpoints.learning.corpus     import CorpusEndpoint
from endpoints.learning.prediction import PredictionEndpoint
from endpoints.learning.extractors.tally     import TallyEndpoint
from endpoints.learning.extractors.embedding import EmbeddingEndpoint
from endpoints.learning.extractors.bert      import BertEndpoint
from endpoints.learning.extractors.bow       import BOWEndpoint

class DebateServer():

    influence_cache = {}

    def __init__(self, config):
        self.config = config
        # Basic data structure endpoints
        self.users = UserEndpoint(self)
        self.discussions = DiscussionEndpoint()
        self.outcomes = OutcomeEndpoint()
        self.votes = VoteEndpoint()
        self.comments = CommentEndpoint()
        self.nominations = NominationEndpoint()

        # Convenience function endpoints
        self.util = UtilitiesEndpoint(self)
        self.math = MathEndpoint()

        # Research-enabling endpoints
        self.analysis = AnalysisEndpoint(self)

        # Machine Learning endpoints
        self.instances = InstanceEndpoint(self)
        self.vectors = VectorEndpoint(self)
        self.corpora = CorpusEndpoint(self)
        self.prediction = PredictionEndpoint(self)

        # Feature extractors
        extractor_options = config["extractors"]
        extractors = []
        if "TALLY" in extractor_options:
            extractors.append(TallyEndpoint(self))
        if "BOW" in extractor_options:
            extractors.append(BOWEndpoint(self))
        if "BERT" in extractor_options:
            extractors.append(BertEndpoint(self))
            self.import_bert_cache()
        if "GLOVE" in extractor_options:
            extractors.append(EmbeddingEndpoint(self))
        self.extractors = extractors
        filename = config["source"]
        start = time.time()
        self.import_corpus(filename)
        end = time.time()
        print("{} seconds elapsed while importing full corpus.".format((end-start)))

    def import_bert_cache(self):
        print("IMPORTING INFLUENCE")
        if len(DebateServer.influence_cache.keys()) == 0:
            print("INFLUENCE CACHE IS NONE")
            cachepath = os.path.join("..","cache","bert_clean")
            if (os.path.exists(cachepath)):
                categories = os.listdir(cachepath)
                for cat in categories:
                    print(cat)
                    if not os.path.isfile(cat):
                        catpath = os.path.join(cachepath, cat)
                        if os.path.exists(catpath):
                            subcat = os.listdir(catpath)
                            for sub in subcat:
                                subcatpath = os.path.join(catpath, sub)
                                if os.path.isfile(subcatpath) and "DS_Store" not in sub:
                                    print(subcatpath)
                                    cache_file = open(subcatpath, "r")
                                    cache_line = cache_file.readline()
                                    old_cache_line = None
                                    line_type = 'content'
                                    current_key = None
                                    if len(cache_line) > 0:
                                        current_key = int(cache_line)
                                    while current_key is not None and cache_line != old_cache_line:
                                        old_cache_line = cache_line
                                        cache_line = cache_file.readline().strip()
                                        if line_type == 'content':
                                            if len(cache_line) > 0:
                                                cache_json = json.loads(cache_line)
                                                DebateServer.influence_cache[current_key] = cache_json
                                                if current_key % 100 == 0:
                                                    print("Keyed {}".format(current_key))
                                            line_type = 'blank'
                                        elif line_type == 'key':
                                            if len(cache_line) > 0:
                                                current_key = int(cache_line)
                                            line_type = 'content'
                                        elif line_type == 'blank':
                                            line_type = 'key'
                                            

                                        
    def import_corpus(self, filename, min=0, max=500000, load_cached_influences=True):
        corpus_file = open(filename, "r")
        corpus_json = json.loads(corpus_file.read())
        count_notices = 0
        count_relists = 0
        if "Discussions" in corpus_json.keys():
            for disc in corpus_json["Discussions"]:
                if "Title" in disc.keys() and len(disc["Title"]) > 0:
                    code, discussion_id = self.discussions.post_discussion(disc)
        if "Users" in corpus_json.keys():
            for user in corpus_json["Users"]:
                code, user_id = self.users.post_user(user)
        if "Outcomes" in corpus_json.keys():
            for outcome in corpus_json["Outcomes"]:
                code, new_outcome_id = self.outcomes.post_outcome(outcome)
                code, new_outcome_timestamp = self.outcomes.get_timestamp(new_outcome_id)
                if new_outcome_timestamp != -1:
                    code, outcome_discussion_id = self.outcomes.get_discussion_id(new_outcome_id)
                    self.discussions.put_contribution(outcome_discussion_id, new_outcome_id, new_outcome_timestamp)
        if "Contributions" in corpus_json.keys():
            for contrib in corpus_json["Contributions"]:
                if "ID" in contrib.keys():
                    this_id = contrib["ID"]
                    is_vote = self.util.is_vote(this_id)
                    if is_vote:
                        code, new_vote_id = self.votes.post_vote(contrib)
                        code, new_vote_timestamp = self.votes.get_timestamp(new_vote_id)
                        if new_vote_timestamp != -1:
                            code, vote_discussion_id = self.votes.get_discussion_id(new_vote_id)
                            self.discussions.put_contribution(vote_discussion_id, new_vote_id, new_vote_timestamp)
                            
                            # Define success
                            normalized = self.config["normalized"]
                            code, outcome_id = self.discussions.get_outcome_id(vote_discussion_id)
                            code, outcome_label = self.outcomes.get_label(outcome_id, normalized=normalized)
                            code, vote_label = self.votes.get_label(new_vote_id, normalized=normalized)
                            success = (outcome_label == vote_label)
                            self.votes.put_success(new_vote_id, success)

                        code, new_user_id = self.votes.get_user_id(new_vote_id)
                        if code == 200:
                            code, new_user_id = self.users.put_contribution_id(new_user_id, new_vote_id, new_vote_timestamp)
                    
                    is_comment = self.util.is_comment(this_id)
                    if is_comment:
                        code, new_comment_id = self.comments.post_comment(contrib)
                        code, new_comment_timestamp = self.comments.get_timestamp(new_comment_id)
                        if new_comment_timestamp != -1:
                            code, comment_discussion_id = self.comments.get_discussion_id(new_comment_id)
                            self.discussions.put_contribution(comment_discussion_id, new_comment_id, new_comment_timestamp)
                        code, new_user_id = self.comments.get_user_id(new_comment_id)
                        if code == 200:
                            code, new_user_id = self.users.put_contribution_id(new_user_id, new_comment_id, new_comment_timestamp)
                    
                    is_nomination = self.util.is_nomination(this_id)
                    if is_nomination:
                        code, new_nomination_id = self.nominations.post_nomination(contrib)
                        code, new_nomination_timestamp = self.nominations.get_timestamp(new_nomination_id)
                        if new_nomination_timestamp != -1:
                            code, nomination_discussion_id = self.nominations.get_discussion_id(new_nomination_id)
                            self.discussions.put_contribution(nomination_discussion_id, new_nomination_id, new_nomination_timestamp)
                        code, new_user_id = self.nominations.get_user_id(new_nomination_id)
                        if code == 200:
                            code, new_user_id = self.users.put_contribution_id(new_user_id, new_nomination_id, new_nomination_timestamp)

        if "Citations" in corpus_json.keys():
            for cite in corpus_json["Citations"]:
                contrib_id = cite["ID"]
                citations = cite["Citations"]
                if self.util.is_vote(contrib_id):
                    code, citations = self.votes.put_citations(contrib_id, citations)
                if self.util.is_comment(contrib_id):
                    code, citations = self.comments.put_citations(contrib_id, citations)
                if self.util.is_nomination(contrib_id):
                    code, citations = self.nominations.put_citations(contrib_id, citations)

        self.users.put_sort_contributions()
        self.discussions.put_sort_contributions()
        
        if load_cached_influences:
            influences_loaded = 0
            for i in range(1,21):
                csv_in = open("cached_influences_offset_{}.csv".format(i), "r")
                read = csv.reader(csv_in)
                for row in read:
                    if len(row) >= 2 and len(row[1]) > 0:
                        contrib_id, inf = int(row[0]), float(row[1])
                        if self.util.is_vote(contrib_id):
                            self.votes.put_influence(contrib_id, inf)
                            influences_loaded += 1
                        if self.util.is_comment(contrib_id):
                            self.comments.put_influence(contrib_id, inf)
                            influences_loaded += 1
            print("Loaded {} influences from cache.".format(influences_loaded))
        code, discs = self.discussions.get_all()
        print("{} discs found".format(len(discs)))
import os, re, csv, json, time, datetime
import pickle
from collections import defaultdict
from endpoints.data.discussion import DiscussionEndpoint
from endpoints.data.user       import UserEndpoint
from endpoints.data.outcome    import OutcomeEndpoint
from endpoints.data.vote       import VoteEndpoint
from endpoints.data.comment    import CommentEndpoint
from endpoints.data.nomination import NominationEndpoint
from endpoints.helpers.utilities import UtilitiesEndpoint
from endpoints.helpers.analysis  import AnalysisEndpoint
from endpoints.learning.instance   import InstanceEndpoint
from endpoints.learning.vector     import VectorEndpoint
from endpoints.learning.corpus     import CorpusEndpoint
from endpoints.learning.prediction import PredictionEndpoint
from endpoints.learning.extractors.tally     import TallyEndpoint
from endpoints.learning.extractors.volume    import VolumeEndpoint
from endpoints.learning.extractors.embedding import EmbeddingEndpoint
from endpoints.learning.extractors.bert      import BertEndpoint, import_bert_cache
from endpoints.learning.extractors.bow       import BOWEndpoint

class DebateServer():

    influence_cache = {}

    def __init__(self, config, use_pickle=False):
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
        if "VOLUME" in extractor_options:
            extractors.append(VolumeEndpoint(self))
        if "BOW" in extractor_options:
            extractors.append(BOWEndpoint(self))
        if "BERT" in extractor_options:
            extractors.append(BertEndpoint(self))
            if len(DebateServer.influence_cache.keys()) == 0:
                DebateServer.influence_cache = import_bert_cache()
        if "GLOVE" in extractor_options:
            extractors.append(EmbeddingEndpoint(self))
        self.extractors = extractors
        filename = config["source"]
        start = time.time()
        print("Importing corpus")
        if use_pickle and os.path.exists("pickles/votes.pickle"):
            print("Importing from pickles")
            self.import_from_pickle()
        else:
            self.import_corpus(filename, load_cached_influences=config["cached_influences"])

            if use_pickle:
                pickle.dump( self.votes, open( "pickles/votes.pickle", "wb" ) )
                pickle.dump( self.users, open( "pickles/users.pickle", "wb" ) )
                pickle.dump( self.discussions, open( "pickles/discussions.pickle", "wb" ) )
                pickle.dump( self.outcomes, open( "pickles/outcomes.pickle", "wb" ) )
                pickle.dump( self.comments, open( "pickles/comments.pickle", "wb" ) )
                pickle.dump( self.nominations, open( "pickles/nominations.pickle", "wb" ) )
        end = time.time()
        print("{:2.2f} seconds elapsed while importing full corpus.".format((end-start)))

    def import_from_pickle(self):
        if os.path.exists("pickles/votes.pickle"):
            self.votes = pickle.load(open("pickles/votes.pickle", "rb"))

        if os.path.exists("pickles/users.pickle"):
            self.users = pickle.load(open("pickles/users.pickle", "rb"))

        if os.path.exists("pickles/discussions.pickle"):
            self.discussions = pickle.load(open("pickles/discussions.pickle", "rb"))

        if os.path.exists("pickles/outcomes.pickle"):
            self.outcomes = pickle.load(open("pickles/outcomes.pickle", "rb"))

        if os.path.exists("pickles/comments.pickle"):
            self.comments = pickle.load(open("pickles/comments.pickle", "rb"))

        if os.path.exists("pickles/nominations.pickle"):
            self.nominations = pickle.load(open("pickles/nominations.pickle", "rb"))

                                        

    def import_corpus(self, filename, min=0, max=500000, load_cached_influences=True):
        source_path = os.path.join("jsons")
        dir_exists = os.path.exists(source_path)
        if not dir_exists:
            os.makedirs("jsons")
        source_path = os.path.join("jsons", filename)
        if not os.path.isfile(source_path):
            print("Fetching corpus")
            
            if os.path.exists('jsons') and not os.path.isfile('jsons/afd_2019_full_policies.json'):
                url = 'https://afdcorpus.s3.amazonaws.com/afd_2019_full_policies.json'

                self.util.download_corpus(url)

        else:
            print("Corpus already downloaded locally.")
        start = time.time()
        corpus_file = open(source_path, "r")
        corpus_json = json.loads(corpus_file.read())
        now = time.time()
        print("{:2.2f} Loaded from JSON.".format((now-start)))
        start = now
        count_notices = 0
        count_relists = 0

        """
        Post all the discussions, one at a time
        """
        if "Discussions" in corpus_json.keys():
            for disc in corpus_json["Discussions"]:
                if "Title" in disc.keys() and len(disc["Title"]) > 0:
                    code, discussion_id = self.discussions.post_discussion(disc)
        now = time.time()
        print("{:2.2f} Posted all discussions.".format((now-start)))
        start = now

        """
        Load user demographic profiles
        """
        user_demographics = self.import_user_demographics()

        """
        Post all the users, one at a time
        """
        if "Users" in corpus_json.keys():
            for user in corpus_json["Users"]:
                code, user_id = self.users.post_user(user)
                username = user["Name"]
                if username in user_demographics.keys():
                    self.users.put_demographics(user_id, user_demographics[username])


        now = time.time()
        print("{:2.2f} Posted all users and demographics.".format((now-start)))
        start = now
        
        """
        Post all the outcomes, one at a time
        """
        if "Outcomes" in corpus_json.keys():
            for outcome in corpus_json["Outcomes"]:
                code, new_outcome_id = self.outcomes.post_outcome(outcome)
                code, new_outcome_timestamp = self.outcomes.get_timestamp(new_outcome_id)
                if new_outcome_timestamp != -1:
                    code, outcome_discussion_id = self.outcomes.get_discussion_id(new_outcome_id)
                    self.discussions.put_contribution(outcome_discussion_id, new_outcome_id, new_outcome_timestamp)
        now = time.time()
        print("{:2.2f} Posted all outcomes.".format((now-start)))
        start = now

        """
        Post all the votes and comments, one at a time
        """
        if "Contributions" in corpus_json.keys():
            for contrib in corpus_json["Contributions"]:
                if "ID" in contrib.keys():
                    this_id = contrib["ID"]

                    is_vote = self.util.is_vote(this_id)
                    is_comment = self.util.is_comment(this_id)
                    is_nomination = self.util.is_nomination(this_id)

                    if is_vote:
                        self.votes.post_vote(contrib)
                    elif is_comment:
                        self.comments.post_comment(contrib)
                    elif is_nomination:
                        self.nominations.post_nomination(contrib)

                    code, this_timestamp = self.util.get_timestamp(this_id)
                    code, this_user_id = self.util.get_user_id(this_id)
                    if code == 200:
                        self.users.put_contribution_id(this_user_id, this_id, this_timestamp)

                    code, this_discussion_id = self.util.get_discussion_id(this_id)
                    if code == 200:
                        self.discussions.put_contribution(this_discussion_id, this_id, this_timestamp)
                        if is_vote:
                            normalized = self.config["normalized"]
                            code, outcome_id = self.discussions.get_outcome_id(this_discussion_id)
                            code, outcome_label = self.outcomes.get_label(outcome_id, normalized=normalized)
                            code, vote_label = self.votes.get_label(this_id, normalized=normalized)
                            success = (outcome_label == vote_label)
                            self.votes.put_success(this_id, success)
        now = time.time()
        print("{:2.2f} Posted all votes, comments, and nominations.".format((now-start)))
        start = now

        """
        Post all the citations, one at a time.
        """    
        if "Citations" in corpus_json.keys():
            for cite in corpus_json["Citations"]:
                contrib_id = cite["ID"]
                citations = cite["Citations"]
                code, citations = self.util.put_citations(contrib_id, citations)
        now = time.time()
        print("{:2.2f} Posted all citations.".format((now-start)))
        start = now

        """
        Sort the user- and discussion-specific sublists of contribution by timestamp.
        """
        self.users.put_sort_contributions()
        self.discussions.put_sort_contributions()
        now = time.time()
        print("{:2.2f} Sorted contributions.".format((now-start)))
        start = now

        """
        Define first-time users
        """
        code, users = self.users.get_all()
        for user_id in users:
            code, first_contrib_id = self.users.get_first_contribution(user_id)
            code, disc_id = self.util.get_discussion_id(first_contrib_id)
            self.users.put_first_discussion(user_id, disc_id)

        now = time.time()
        print("{:2.2f} Found first contributions.".format((now-start)))
        start = now

        """
        Load preprocessed influence measures from disk.
        """
        if load_cached_influences:
            influences_loaded = 0
            for i in range(1,21):
                csv_in = open("forecast_shifts/cached_influences_offset_{}.csv".format(i), "r")
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
            now = time.time()
            print("{:2.2f} Loaded influences from disk.".format((now-start)))
            start = now

        code, discs = self.discussions.get_all()
        now = time.time()
        print("{:2.2f} Loaded all discussions from disk.".format((now-start)))
        start = now

    def import_user_demographics(self):
        demo_csv = csv.reader(open("afd_genders_tenures.csv", "r"))
        row_number = 0
        headers = {}
        demographics = defaultdict(lambda: {})

        genders_count = defaultdict(int)
        timestamps_count = 0

        date_format = "%Y-%m-%dT%H:%M:%SZ"
        ipv4_match = "\d+\.\d+\.\d+\.\d+"
        ipv6_match = "\w+:\w+:\w+:\w+:\w+:\w+:\w+:\w+"

        for row in demo_csv:
            if row_number == 0:
                for i, cell in enumerate(row):
                    print(cell)
                    headers[cell] = i
            else:
                username_index = headers["username"]
                username = row[username_index]
                gender_index = headers["gender"]
                gender = row[gender_index]
                if "male" in gender:
                    demographics[username]["gender"] = gender
                    genders_count[gender] = genders_count[gender] + 1
                signup_index = headers["signup"]
                signup_string = row[signup_index].strip()
                if len(signup_string) > 0:
                    parse_object = datetime.datetime.strptime(signup_string, date_format)
                    timestamp = parse_object.timestamp()
                    demographics[username]["signup"] = timestamp
                    timestamps_count += 1
                elif re.match(ipv4_match, username) or re.match(ipv6_match, username):
                    demographics[username]["signup"] = -1
                
                count_index = headers["editcount"]
                count = row[count_index]
                if len(count) > 0:
                    count = int(count)
                else:
                    count = -1
                demographics[username]["editcount"] = count

            row_number += 1
        return demographics

        

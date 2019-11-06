import os, json, time      
import pandas as pd

"""
TODO:
- Sorted list of contributions, by timestamp, per user
- Sorted list of contributions, by timestamp, per discussion
- Identify first-time contributions
- Load forecast shift, per contribution, from disk
"""


def calculate_success():
    votes_df = pd.read_csv("afd1.1/votes_df.csv")
    outcomes_df = pd.read_csv("afd1.1/outcomes_df.csv")
    outcomes_df["discussion_id"] = outcomes_df["parent"]
    outcomes_results = outcomes_df.loc[:, ["parent", "label"]]
    outcomes_results.columns = ["discussion_id", "outcome"]
    votes_df_merge = votes_df.merge(outcomes_results, on="discussion_id", how="left")
    votes_df_merge["success"] = votes_df_merge["label"] == votes_df_merge["outcome"]
    print(votes_df_merge["success"].shape)
    with open("votes_success_df.csv", "w") as votes_out:
        votes_out.write(votes_df_merge.to_csv())



def reshape_demographics():
    users_df = pd.read_csv("afd1.1/users_df.csv")
    diyi_df = pd.read_csv("afd_genders_tenures.csv")
    print(users_df.shape)
    diyi_df = diyi_df.loc[:, ["name", "editcount", "signup", "emailable", "gender"]]
    merge_df = users_df.merge(diyi_df, on="name", how="left")
    clean_merge = merge_df.loc[:, ["user_id", "name", "editcount", "signup", "gender"]]
    print(clean_merge.shape)
    clean_merge = clean_merge.drop_duplicates()
    print(clean_merge.shape)
    with open("afd1.1/users_merge_df.csv", "w") as out_file:
        out_file.write(clean_merge.to_csv()) 
    

"""
Ensure that our corpus exists as a local copy. Download from an S3 bucket otherwise.
"""
def confirm_corpus_exists(data_folder, full_filename):
    dir_exists = os.path.exists(data_folder)
    if not dir_exists:
        os.makedirs(data_folder)
    source_path = os.path.join(data_folder, full_filename)
    if not os.path.isfile(source_path):
        print("Fetching corpus")
        if not os.path.isfile(os.path.join(data_folder, full_filename)):
            url = f"https://afdcorpus.s3.amazonaws.com/{full_filename}"
            self.util.download_corpus(url)
    else:
        print("Corpus already downloaded locally.")
    return source_path


def generate_from_json():
    data_folder = "jsons"
    full_filename = "afd_2019_full_policies.json"
    source_path = confirm_corpus_exists(data_folder, full_filename)
    raw = json.loads(open(source_path).read())

    generators = [generate_citations]
    for i, func in enumerate(generators):
        start = time.time()
        func(raw)
        end = time.time()
        print(f"{i} in {(end-start):.3f} seconds")

def generate_citations(raw):
    if "Citations" in raw:
        cite_dict = {'citation': [], 'contrib_id': []}
        for cite in raw["Citations"]:
            contrib_id = cite["ID"]
            if contrib_id and "Citations" in cite and cite["Citations"]:
                for literal_cite in cite["Citations"]:
                    cite_dict['citation'].append(literal_cite)
                    cite_dict['contrib_id'].append(contrib_id)
        cite_df = pd.DataFrame.from_dict(cite_dict)
        index = 900000001
        cite_master = {'cite_id': [], 'citation': []}
        master_dict = {}
        for i, cite in enumerate(cite_df["citation"].unique()):
            cite_master['cite_id'].append(index+i)
            cite_master['citation'].append(cite)
            master_dict[cite] = index+i

        cite_master_df = pd.DataFrame.from_dict(cite_master)
        print(cite_master_df.shape)

        with open("citations_master.csv", "w") as cite_master_out:
            cite_master_out.write(cite_master_df.to_csv())

        cite_ids = [master_dict[c] for c in cite_df["citation"]]

        cite_df["cite_id"] = cite_ids

        cite_final = cite_df.loc[:, ["contrib_id", "cite_id"]]
        with open("citations_df.csv", "w") as cite_out:
            cite_out.write(cite_final.to_csv())

        

def generate_discussions(raw):
    if "Discussions" in raw:
        disc_dict = {'title':[], 'disc_id':[]}
        for i, disc in enumerate(raw["Discussions"]):
            if "Title" in disc and "ID" in disc:
                disc_dict["title"].append(disc["Title"])
                disc_dict["disc_id"].append(int(disc["ID"]))
        disc_df = pd.DataFrame.from_dict(disc_dict)
    with open("discussions_df.csv", "w") as disc_out:
        disc_out.write(disc_df.to_csv())
    
def generate_users(raw):
    if "Users" in raw:
        users_dict = {'name':[], 'user_id':[]}
        for i, user in enumerate(raw["Users"]):
            if "Name" in user and "ID" in user:
                users_dict["name"].append(user["Name"])
                users_dict["user_id"].append(int(user["ID"]))
        users_df = pd.DataFrame.from_dict(users_dict)
    with open("users_df.csv", "w") as users_out:
        users_out.write(users_df.to_csv())
      
def generate_outcomes(raw):
    if "Outcomes" in raw:
        outcomes_dict = {'outcome_id': [], 'parent': [], 'timestamp': [], 'user_id': [], 'label': [], 'raw': [], 'rationale': []}
        for i, outcome in enumerate(raw["Outcomes"]):
            if "ID" in outcome:
                outcome_id = None if "ID" not in outcome else int(outcome["ID"])
                parent = None if "Parent" not in outcome else int(outcome["Parent"])
                timestamp = None if "Timestamp" not in outcome or not outcome["Timestamp"] else int(outcome["Timestamp"])
                user_id = None if "User" not in outcome else int(outcome["User"])
                label = None if "Label" not in outcome else outcome["Label"]
                raw = None if "Raw" not in outcome else outcome["Raw"]
                rationale = None if "Rationale" not in outcome else outcome["Rationale"]

                outcomes_dict["outcome_id"].append(outcome_id)
                outcomes_dict["parent"].append(parent)
                outcomes_dict["timestamp"].append(timestamp)
                outcomes_dict["user_id"].append(user_id)
                outcomes_dict["label"].append(label)
                outcomes_dict["raw"].append(raw)
                outcomes_dict["rationale"].append(rationale)
        outcomes_df = pd.DataFrame.from_dict(outcomes_dict)
    with open("outcomes_df.csv", "w") as outcomes_out:
        outcomes_out.write(outcomes_df.to_csv())
      
def generate_contributions(raw):
    if "Contributions" in raw:
        votes_dict = {'vote_id': [], 'parent': [], 'discussion_id': [], 'timestamp': [], 'user_id': [], 'label': [], 'raw': [], 'rationale': []}
        comments_dict = {'comment_id': [], 'parent': [], 'discussion_id': [], 'timestamp': [], 'user_id': [], 'text': []}
        nominations_dict = {'nomination_id': [], 'parent': [], 'discussion_id': [], 'timestamp': [], 'user_id': [], 'text': []}
    for i, contrib in enumerate(raw["Contributions"]):
        if "ID" in contrib:
            contrib_str = str(contrib["ID"])
            contrib_id = None if "ID" not in contrib else int(contrib["ID"])
            parent = None if "Parent" not in contrib else int(contrib["Parent"])
            timestamp = None if "Timestamp" not in contrib or not contrib["Timestamp"] else int(contrib["Timestamp"])
            user_id = None if "User" not in contrib else int(contrib["User"])
            discussion_id = None if "Discussion" not in contrib else int(contrib["Discussion"])

            if "4" == contrib_str[0]:
                votes_dict["vote_id"].append(contrib_id)
                votes_dict["parent"].append(parent)
                votes_dict["discussion_id"].append(discussion_id)
                votes_dict["timestamp"].append(timestamp)
                votes_dict["user_id"].append(user_id)
                label = None if "Label" not in contrib else contrib["Label"]
                raw = None if "Raw" not in contrib else contrib["Raw"]
                rationale = None if "Rationale" not in contrib else contrib["Rationale"]
                votes_dict["label"].append(label)
                votes_dict["raw"].append(raw)
                votes_dict["rationale"].append(rationale)
            else:
                text = None if "Text" not in contrib else contrib["Text"]
                if "5" == contrib_str[0]:
                    comments_dict["comment_id"].append(contrib_id)
                    comments_dict["parent"].append(parent)
                    comments_dict["discussion_id"].append(discussion_id)
                    comments_dict["timestamp"].append(timestamp)
                    comments_dict["user_id"].append(user_id)
                    comments_dict["text"].append(text)
                elif "6" == contrib_str[0]:
                    nominations_dict["nomination_id"].append(contrib_id)
                    nominations_dict["parent"].append(parent)
                    nominations_dict["discussion_id"].append(discussion_id)
                    nominations_dict["timestamp"].append(timestamp)
                    nominations_dict["user_id"].append(user_id)
                    nominations_dict["text"].append(text)
    votes_df = pd.DataFrame.from_dict(votes_dict)
    comments_df = pd.DataFrame.from_dict(comments_dict)
    nominations_df = pd.DataFrame.from_dict(nominations_dict)
    with open("votes_df.csv", "w") as votes_out:
        votes_out.write(votes_df.to_csv())
    with open("comments_df.csv", "w") as comments_out:
        comments_out.write(comments_df.to_csv())
    with open("nominations_df.csv", "w") as nominations_out:
        nominations_out.write(nominations_df.to_csv())
      


def old_import():
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

if __name__ == "__main__":
    get_contribs_by_user()
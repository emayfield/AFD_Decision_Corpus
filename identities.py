import time
import csv
import math
from collections import defaultdict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from endpoints.helpers.cache import store, lookup
import operator
import os
from server import DebateServer
import numpy as np
import csv

def www(server, normalized):
    # We first analyze only conversations that have one 
    code, discussions = get_strict_discussions(server)
    suffix = "activity_and_index"

    profiles(server, discussions)

def profiles(server, discussions):
    keys_to_successes = defaultdict(lambda: [])
    for disc_id in discussions:
        code, contrib_ids = server.discussions.get_contributions(disc_id)
        if disc_id % 1000 == 0:
            print("Processing discussion {}".format(disc_id))

        contribs_to_users = {}
        users_to_contribs = defaultdict(lambda: [])
        for i, contrib_id in enumerate(contrib_ids):
            code, user_id = server.util.get_user_id(contrib_id)
            code, timestamp = server.util.get_timestamp(contrib_id)

            contribs_to_users[contrib_id] = user_id
            users_to_contribs[user_id].append(contrib_id)


        for user_id in users_to_contribs:
            details = {}
            success = check_success(users_to_contribs[user_id])
            code, gender = server.users.get_gender(user_id)
            if code == 200:
                details["gender"] = gender

            code, registered = server.users.is_registered(user_id)
            if code == 200 and not registered:
                details["gender"] = "unregistered"

            code, edit_count = server.users.get_edit_count(user_id)
            if code == 200:
                details["enfranchised"] = (edit_count is not None and edit_count > 250)

            code, first_time = server.util.first_time_user(server, user_id, disc_id)
            if code == 200:
                details["first_time"] = first_time

            key = get_user_key(details)
            keys_to_successes[key].append(success)

    for key in keys_to_successes:
        positive = 0
        total = 0
        for event in keys_to_successes[key]:
            if event:
                positive += 1
            total += 1
        print(f"{key} {positive} / {total} = {(positive/total)}")

"""
"""
def get_user_key(details):
    keyA = "unknown"
    gender = ""
    first_time = ""
    enfranchised = ""
    if "gender" in details.keys():
        gender = details["gender"]
    if "first_time" in details.keys():
        if details["first_time"]:
            first_time = "newcomer"
        else:
            first_time = "veteran"
    if "enfranchised" in details.keys():
        if details["enfranchised"]:
            enfranchised = "Wikipedian"
    keyA = "{} {} {}".format(gender, enfranchised, first_time)
    return keyA

def check_success(user_contribs, calculate_forecast_shift=False):
    cume_inf = 0.0
    max_success = 0
    latest_label = ""
    for contrib_id in user_contribs:
        influence = 0
        if server.util.is_vote(contrib_id):
            code, this_success = server.votes.get_success(contrib_id)
            if this_success is not None:
                max_success = max(max_success, this_success)
            code, label = server.votes.get_label(contrib_id, normalized=normalized)
            latest_label = label
            if calculate_forecast_shift:
                code, influence = server.votes.get_influence(contrib_id)
        if calculate_forecast_shift and server.util.is_comment(contrib_id):
            code, influence = server.comments.get_influence(contrib_id)
        if calculate_forecast_shift and influence is not None:
            cume_inf += influence
    return max_success > 0

def get_strict_discussions(server):
    timestamp_cutoffs = {}
    for y in range(2005,2019):
        code, cutoffs = server.util.get_timestamps_for_year(y)
        timestamp_cutoffs[y] = cutoffs

    code, discussion_ids = server.discussions.get_all()
    total_skipped = 0
    skip_codes = {}
    filtered_discussion_ids = []
    for disc_id in discussion_ids:
        year = server.util.get_year(server, disc_id, timestamp_cutoffs)

        code, original_contrib_ids = server.discussions.get_contributions(disc_id)
        skip_empty = server.config["strict_discussions"]
        add = False
        if not skip_empty:
            add = True
        else:
            has_vote = False
            has_nom = False
            has_out = False
            for orig_id in original_contrib_ids:
                is_vote = server.util.is_vote(orig_id)
                is_nom = server.util.is_nomination(orig_id)
                is_outcome = server.util.is_outcome(orig_id)
                if is_vote:
                    has_vote = True
                if is_nom:
                    has_nom = True
                if is_outcome:
                    has_out = True
            if (has_vote and has_out):
                filtered_discussion_ids.append(disc_id)
            else:
                if not has_out:
                    c = "no_out"
                elif not has_vote:
                    c = "no_vote"
                if c not in skip_codes.keys():
                    skip_codes[c] = 0
                skip_codes[c] = skip_codes[c] + 1
                total_skipped += 1
    print("Filtered out {} discussions, {} remain.".format(total_skipped, len(filtered_discussion_ids)))
    for c in skip_codes.keys():
        print("   Filtered from {}: {}".format(c, skip_codes[c]))
    return 201, filtered_discussion_ids

def get_examples(server, discussions, key):
    for disc_id in discussions:
        code, title = server.discussions.get_title(disc_id)
        code, contribs = server.discussions.get_contributions(disc_id)

        if False:
            # Find by vote patterns
            first_vote = contribs[0]
            second_vote = contribs[1]
            if server.util.is_vote(first_vote) and server.util.is_vote(second_vote):
                first_label = server.votes.get_label(first_vote)
                second_label = server.votes.get_label(second_vote)
                if first_label=="Keep" and second_label == "Delete":
                    print(title)
        # Find by citation
        for contrib_id in contribs:
            if server.util.is_vote(contrib_id):
                code, cites = server.votes.get_citations(contrib_id)
                if key in cites:
                    print(title)


"""
Utility function to define how to carve up votes for various tests.
Change this to subdivide the corpus in interesting ways!
"""
def get_key(details):
    label = ""
    year = ""
    order = ""
    user = ""
    citation = ""
    tenure = ""
    active = ""
    index = ""
    wait = ""
    if "label" in details.keys():
        label = details["label"]
    if "year" in details.keys():
        year = details["year"]
    if "order" in details.keys():
        order = details["order"]
    if "user" in details.keys():
        user = details["user"]
    if "citation" in details.keys():
        citation = details["citation"]
    if "tenure" in details.keys():
        tenure = details["tenure"]
    if "active" in details.keys():
        active = details["active"]
    if "wait" in details.keys():
        wait = details["wait"]
    if "index" in details.keys():
        index = details["index"]

    keyA = "{} {}".format(label, active)
    """DON'T FORGET TO CHANGE THE SUFFIX"""

    """REMEMBER TO CHECK IF YOU'RE ITERATING CITATIONS"""
    return [keyA]



if __name__ == "__main__":
    normalized = 2
    config = {
        "extractors": ["TALLY"],
        "normalized": normalized,
        "strict_discussions": True,
        "source": "jsons/afd_2019_full_policies.json"
    }
    initialize = time.time()
    server = DebateServer(config)
    start = time.time()
    www(server, normalized)
    end = time.time()
    print(f"{(start-initialize)} to initialize, {(end-start)} seconds for processing request.")

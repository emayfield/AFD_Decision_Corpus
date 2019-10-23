import time
import csv
import math
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from endpoints.helpers.cache import store, lookup
import operator
import os
from server import DebateServer
import numpy as np
import csv

def cscw(server, normalized):
    # We first analyze only conversations that have one 
    code, discussions = get_strict_discussions(server)


    suffix = "activity_and_index"

#    analyze_by_user(server, discussions)
#    analyze_by_session(suffix, server, discussions, normalized, cutoff=10)
    print_label_counts_with_keys(suffix, server, discussions, normalized)
#    get_examples(server, discussions, "article size")
#    aggregate_stats(server, discussions)
    if False:
        margins = {}
        all_outcomes = {}
        for disc_id in discussions:
            if disc_id % 1000 == 0:
                print(disc_id)
            code, contribs = server.discussions.get_contributions(disc_id)
            keeps = 0
            deletes = 0
            for c_id in contribs:
                if server.util.is_vote(c_id):
                    code, label = server.votes.get_label(c_id, normalized=normalized)
                    if "Keep" in label:
                        keeps += 1
                    if "Delete" in label:
                        deletes += 1
            margin = deletes-keeps
            code, outcome_id = server.discussions.get_outcome_id(disc_id)
            code, outcome = server.outcomes.get_label(outcome_id, normalized=normalized)
            if margin not in margins.keys():
                margins[margin] = {}
            if outcome not in margins[margin].keys():
                all_outcomes[outcome] = 1
                margins[margin][outcome] = 0
            margins[margin][outcome] = margins[margin][outcome] + 1

        margin_labels = sorted(list(margins.keys()))
        outcome_labels = sorted(list(all_outcomes.keys()))
        margin_out = open("outcomes_by_margins.csv", "w")
        margin_csv = csv.writer(margin_out)
        headers = ["margin"]
        for o in outcome_labels:
            headers.append(o)
        margin_csv.writerow(headers)
        for m in margin_labels:
            row = [m]
            for o in outcome_labels:
                freq = 0
                if o in margins[m].keys():
                    freq = margins[m][o]
                row.append(freq)
            margin_csv.writerow(row)


        code, users = server.users.get_all()
        users_by_contrib_count = {}
        print("Users: {}".format(len(users)))
        for user_id in users:
            code, user = server.users.get_by_id(user_id)
            key = len(user.contributions)
            if key not in users_by_contrib_count.keys():
                print("Added key {}".format(key))
                users_by_contrib_count[key] = []
            users_by_contrib_count[key].append(user.name)
        counts = sorted(list(users_by_contrib_count.keys()))
        usernames_file = open("users_by_activity.csv", "w")
        csv_out = csv.writer(usernames_file)
        headers = ["username","contributions"]
        csv_out.writerow(headers)
        for c in counts:
            for username in users_by_contrib_count[c]:
                row = [username, c]
                csv_out.writerow(row)


def get_session_keys(details):
    activity = ""
    label = ""
    first_order = ""
    avg_wait = ""
    burst_wait = ""
    if "activity" in details.keys():
        activity = details["activity"]
    if "label" in details.keys():
        label = details["label"]
    if "first_order" in details.keys():
        first_order = details["first_order"]
    if "avg_wait" in details.keys():
        avg_wait = details["avg_wait"]
    if "burst_wait" in details.keys():
        burst_wait = details["burst_wait"]

    """ REMEMBER TO CHANGE THE SUFFIX """
    keys = ["{} {}".format(first_order, activity)]
    return keys

def analyze_by_session(suffix, server, discussions, normalized, cutoff=99999):
    outcome_labels = {}
    vote_labels = {}
    comment_labels = {}
    keyed_sessions = {}

    # Preload for by_year=True
    timestamp_cutoffs = {}
    for y in range(2005,2019):
        code, cutoffs = server.util.get_timestamps_for_year(y)
        timestamp_cutoffs[y] = cutoffs

    for disc_id in discussions:
        latest_year = -1
        latest_timestamp = -1
        code, contrib_ids = server.discussions.get_contributions(disc_id)

        disc_votes = {}
        if disc_id % 1000 == 0:
            print("Processing discussion {}".format(disc_id))
        
        contribs_to_users = {}
        users_to_contribs = {}
        users_to_first_order = {}
        contribs_to_wait_times = {}

        votes_so_far = 0
        latest_timestamp = -1
        for i, contrib_id in enumerate(contrib_ids):
            code, user = server.util.get_user_id(contrib_id)

            # Calculate wait times.
            code, timestamp = server.util.get_timestamp(contrib_id)
            wait_time = 0
            if i > 0 and latest_timestamp > 0:
                wait_time = timestamp - latest_timestamp
            contribs_to_wait_times[contrib_id] = wait_time
            if timestamp is not None and timestamp > 0:
                latest_timestamp = timestamp

            contribs_to_users[contrib_id] = user
            if server.util.is_vote(contrib_id):
                votes_so_far += 1
                if user not in users_to_first_order.keys():
                    users_to_first_order[user] = votes_so_far
            if user not in users_to_contribs.keys():
                users_to_contribs[user] = []
            users_to_contribs[user].append(contrib_id)

        for user in users_to_contribs.keys():
            cume_inf = 0.0
            max_success = 0
            latest_label = ""
            wait_times = []
            for contrib in users_to_contribs[user]:
                if type(contribs_to_wait_times[contrib]) is int and contribs_to_wait_times[contrib] > 0:
                    wait_times.append(contribs_to_wait_times[contrib])
                influence = 0
                if server.util.is_vote(contrib):
                    code, this_success = server.votes.get_success(contrib)
                    if this_success is not None:
                        max_success = max(max_success, this_success)
                    code, influence = server.votes.get_influence(contrib)
                    code, label = server.votes.get_label(contrib, normalized=normalized)
                    latest_label = label
                if server.util.is_comment(contrib):
                    code, influence = server.comments.get_influence(contrib)
                if influence is not None:
                    cume_inf += influence
            
            code, username = server.users.get_name(user)

            order = "Commenter"
            if user in users_to_first_order.keys():
                order = users_to_first_order[user]
            details = {
                "user":username,
                "activity":len(users_to_contribs[user]),
                "first_order":order,
                "label":latest_label
            }

#            print("{}: {} waits".format(username, len(wait_times)))
            std = np.std(wait_times)
            mean = np.mean(wait_times)
            if mean > 0:
                burst = std / mean
                details["avg_wait"] = mean
                details["burst_wait"] = burst
                print("{} {} {}".format(username, mean, burst))

            
            if type(order) is str or (order <= cutoff and len(users_to_contribs[user]) <= cutoff) :
                session_keys = get_session_keys(details)
                for k in session_keys:
                    if k not in keyed_sessions.keys():
                        keyed_sessions[k] = {}
                    if disc_id not in keyed_sessions[k].keys():
                        keyed_sessions[k][disc_id] = {}
                    keyed_sessions[k][disc_id]["Type"] = "vote"
                    keyed_sessions[k][disc_id]["Success"] = max_success
                    keyed_sessions[k][disc_id]["Influence"] = cume_inf

    output_file = open("cscw_session_{}.csv".format(suffix), "w")
    output_csv = csv.writer(output_file)
    output_summary_map(output_csv, "Keyed Sessions:", keyed_sessions, min_appearances=20)



def analyze_by_user(server, discussions):
    code, user_ids = server.users.get_all()
    total_users = 0
    total_contribs = 0
    five_or_fewer = 0
    five_or_fewer_contribs = 0
    single_discussion_users = {}
    single_discussion_contribs = 0
    max_contribs = 0
    i = 0
    ranked_users = {}
    for u in user_ids:
        i += 1
        print(u)
        code, contribs = server.users.get_contributions(u)
        strict_contrib_disc_ids = {}
        strict_contrib_ids = contribs
#        for c in contribs:
#            code, disc_id = server.util.get_discussion_id(c)
#            if disc_id in discussions:
#                strict_contrib_disc_ids[disc_id] = 1
#                strict_contrib_ids.append(c)
    if len(strict_contrib_ids) > 0:
        total_users += 1
        total_contribs += len(strict_contrib_ids)
        if len(strict_contrib_ids) <= 5:
            five_or_fewer += 1
            five_or_fewer_contribs += len(strict_contrib_ids)
        if len(strict_contrib_ids) > max_contribs:
            max_contribs = len(strict_contrib_ids)
    ranked_users[u] = len(strict_contrib_ids)
    if ( i % 1000 ) == 0:
        print(i)
    
    ranked_list = sorted(ranked_users.items(), key=lambda x: x[1])
    for i in range(10):
        print(ranked_list[i])
    for i in range(10):
        print(ranked_list[-1*i])
    i = 0
    sum = 0
    while sum < 1647670:
        sum += ranked_list[-1*i][1]
        i += 1
    print("{} users contributed {} times. {} users made five or fewer contribs, total {}. The single busiest user? {}. Single discussion users? {} contributing {}".format(total_users, total_contribs, five_or_fewer, five_or_fewer_contribs, max_contribs, single_discussion_users, single_discussion_contribs))
    print("{} users contributed half of AfD".format(i))

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
#    keyA = "{}".format(order)

    if len(str(active)) > 0 and len(str(index)) > 0:
        if int(active) >= 10:
            active = "Very Active"
        if int(index) >= 10:
            index = "Very Late"

    keyA = "{} {}".format(label, active)

#   For chronological sorting:
#    keyA = "{} {}".format(label, year)

#   For ordering sorting:
#    keyA = "{}".format(tenure) 
#    keyA = "{} {}".format(label, tenure)

#   For user-level sorting
#    keyA = user

#   For impact and success by citation per label
#    keyA = ""
#    if type(order) is int or (len(order) > 0 and int(order) < 6):
#        keyA = "{} {}".format(citation, order)
#    else:
#        keyA = "{} late".format(citation)

#   For overall citation influence
#    keyA = citation
#    keyA = ["{} {}".format(label, c) for c in citation]
#    keyA = "{} {}".format(citation, year)


#    keyA = "{} {}".format(label, active)
    """DON'T FORGET TO CHANGE THE SUFFIX"""

    """REMEMBER TO CHECK IF YOU'RE ITERATING CITATIONS"""
    return [keyA]


def aggregate_stats(server, discussions):
    # Preload for by_year=True
    timestamp_cutoffs = {}
    stats_by_year = {}
    for y in range(2005,2019):
        code, cutoffs = server.util.get_timestamps_for_year(y)
        timestamp_cutoffs[y] = cutoffs
        stats_by_year[y] = {
            "Votes":0,
            "Comments":0,
            "Discussions":0,
            "Citations":0
        }
    
    for disc_id in discussions:
        code, contribs = server.discussions.get_contributions(disc_id)
        num_votes = 0
        num_comments = 0
        num_citations = 0
        latest_year = -1
        for contrib_id in contribs:
            year = -1
            timestamp = -1
            if server.util.is_vote(contrib_id):
                num_votes += 1
                code, timestamp = server.votes.get_timestamp(contrib_id)
                code, citations = server.votes.get_citations(contrib_id)
                for c in citations:
                    num_citations += 1
            if server.util.is_comment(contrib_id):
                code, timestamp = server.comments.get_timestamp(contrib_id)
                code, citations = server.comments.get_citations(contrib_id)
                for c in citations:
                    num_citations += 1
                num_comments += 1
            if server.util.is_nomination(contrib_id):
                code, timestamp = server.nominations.get_timestamp(contrib_id)
                code, citations = server.nominations.get_citations(contrib_id)
                for c in citations:
                    num_citations += 1

            if timestamp is not None and timestamp > -1:
                for y in range(2005, 2019):
                    cutoffs = timestamp_cutoffs[y]
                    if cutoffs[0] <= timestamp < cutoffs[1]:
                        year = y
                latest_year = max(year, latest_year)

        if latest_year is not None and latest_year > -1:
            y = latest_year
            stats_by_year[y]["Votes"] = stats_by_year[y]["Votes"] + num_votes
            stats_by_year[y]["Comments"] = stats_by_year[y]["Comments"] + num_comments
            stats_by_year[y]["Citations"] = stats_by_year[y]["Citations"] + num_citations
            stats_by_year[y]["Discussions"] = stats_by_year[y]["Discussions"] + 1

    aggregates = open("aggregate_stats_by_year.csv", "w")
    csv_agg = csv.writer(aggregates)
    csv_agg.writerow(["Year","Disc","Votes","Comm","Cite","Votes Per", "Comments Per", "Cites Per"])
    for y in range(2005,2019):
        d = stats_by_year[y]["Discussions"]
        v = stats_by_year[y]["Votes"]
        c = stats_by_year[y]["Comments"]
        p = stats_by_year[y]["Citations"]
        csv_agg.writerow([y, d, v, c, p, (v/d), (c/d), (p/d)])

def process_votes(server, timestamp_cutoffs, contrib_id, latest_year, ordinal, latest_timestamp, user_activity, vote_labels, keyed_votes):
    if server.util.is_vote(contrib_id):
        code, v = server.votes.get_label(contrib_id, normalized=normalized)
        code, inf = server.votes.get_influence(contrib_id)
        if inf is None:
            inf = 0

        code, succ = server.votes.get_success(contrib_id)
        code, timestamp = server.votes.get_timestamp(contrib_id)
        code, user_id = server.votes.get_user_id(contrib_id)
        code, username = server.users.get_name(user_id)
        if username is None:
            username = ""
        code, tenure = server.users.get_contributions(user_id)
        if tenure is not None:
            tenure = len(tenure)
        else:
            tenure = ""
#        code, tenure = server.users.get_tenure_at_contribution(user_id, contrib_id)
#        if tenure is None:
#            tenure = ""

        year = -1
        for y in range(2005, 2019):
            cutoffs = timestamp_cutoffs[y]
            if cutoffs[0] <= timestamp < cutoffs[1]:
                year = y
        latest_year = max(year, latest_year)
        
        if v not in vote_labels.keys():
            vote_labels[v] = {}
        if contrib_id not in vote_labels[v].keys():
            vote_labels[v][contrib_id] = {}
        vote_labels[v][contrib_id]["Type"] = "vote"
        vote_labels[v][contrib_id]["Success"] = succ
        vote_labels[v][contrib_id]["Influence"] = inf

        code, citations = server.votes.get_citations(contrib_id)
        if len(citations) == 0:
            citations.append("no citation present")
        
        
        contrib_user_index = user_activity.index(contrib_id)
        user_contrib_count = len(user_activity)
#        for cite in citations:
        details = {
            "year":year,
            "order":ordinal,
            "user":username,
            "citation":citations,
            "tenure":tenure,
            "active":user_contrib_count,
            "index":contrib_user_index,
            "label":v
        }
        all_keys = {}
        keys = get_key(details)
        for key in keys:
            all_keys[key] = 1
                

        for k in all_keys.keys():
            if k not in keyed_votes.keys():
                keyed_votes[k] = {}
            if contrib_id not in keyed_votes[k].keys():
                keyed_votes[k][contrib_id] = {}
            keyed_votes[k][contrib_id]["Type"] = "vote"
            keyed_votes[k][contrib_id]["Success"] = succ
            keyed_votes[k][contrib_id]["Influence"] = inf
            keyed_votes[k][contrib_id]["Order"] = ordinal

    return latest_year, latest_timestamp, vote_labels, keyed_votes


def process_comments(server, timestamp_cutoffs, contrib_id, latest_year, ordinal, latest_timestamp, user_activity, comment_labels, keyed_comments):
    if server.util.is_comment(contrib_id):
        code, timestamp = server.comments.get_timestamp(contrib_id)
        code, user_id = server.comments.get_user_id(contrib_id)
        code, username = server.users.get_name(user_id)
        if username is None:
            username = ""
        code, tenure = server.users.get_contributions(user_id)
        if tenure is not None:
            tenure = len(tenure)
        else:
            tenure = ""
#        code, tenure = server.users.get_tenure_at_contribution(user_id, contrib_id)
#        if tenure is None:
#            tenure = ""

        year = -1
        for y in range(2005, 2019):
            cutoffs = timestamp_cutoffs[y]
            if cutoffs[0] <= timestamp < cutoffs[1]:
                year = y
        latest_year = max(year, latest_year)       
        
        if "comment" not in comment_labels.keys():
            comment_labels["comment"] = {}
        if contrib_id not in comment_labels["comment"].keys():
            comment_labels["comment"][contrib_id] = {}
        comment_labels["comment"][contrib_id]["Type"] = "comment"


        contrib_user_index = user_activity.index(contrib_id)
        user_contrib_count = len(user_activity)

        details = {
            "order":ordinal,
            "user":username,
            "tenure":tenure,
            "active":user_contrib_count,
            "index":contrib_user_index,
            "year":year
        }

        keys = get_key(details)
        for k in keys:
            if k not in keyed_comments.keys():
                keyed_comments[k] = {}
            if contrib_id not in keyed_comments[k].keys():
                keyed_comments[k][contrib_id] = {}
            keyed_comments[k][contrib_id]["Type"] = "comment"
            keyed_comments[k][contrib_id]["Order"] = ordinal
    return latest_year, latest_timestamp, comment_labels, keyed_comments

def process_outcomes(server, outcome_id, latest_year, outcome_labels, keyed_outcomes):
    code, l = server.outcomes.get_label(outcome_id, normalized=normalized)
    code, user_id = server.outcomes.get_user_id(outcome_id)
    code, username = server.users.get_name(user_id)
    if username is None:
        username = ""

    if l not in outcome_labels.keys():
        outcome_labels[l] = {}
    if outcome_id not in outcome_labels[l].keys():
        outcome_labels[l][outcome_id] = {}
    outcome_labels[l][outcome_id]["Type"] = "outcome"


    details = {
        "year":latest_year,
        "user":username,
        "label":l
    }
    keys = get_key(details)
    for k in keys:
        if k not in keyed_outcomes.keys():
            keyed_outcomes[k] = {}
        if outcome_id not in keyed_outcomes[k].keys():
            keyed_outcomes[k][outcome_id] = {}
        keyed_outcomes[k][outcome_id]["Type"] = "outcome"
    return keyed_outcomes

def output_summary_map(writer, header, out_map, min_appearances = 1):
    writer.writerow([header,"Count","Success","Influence","Order"])
    sorted_keys = sorted(list(out_map.keys()))
    for key in sorted_keys:
        count = 0
        avg_succ = 0
        avg_inf = 0
        avg_order = 0
        if len(out_map[key].keys()) >= min_appearances:
            for contrib_id in out_map[key].keys():
                if "Type" in out_map[key][contrib_id].keys():
                    count += 1
                if "Success" in out_map[key][contrib_id].keys():
                    avg_succ += out_map[key][contrib_id]["Success"]
                if "Influence" in out_map[key][contrib_id].keys():
                    avg_inf += out_map[key][contrib_id]["Influence"]
                if "Order" in out_map[key][contrib_id].keys():
                    avg_order += int(out_map[key][contrib_id]["Order"])
            avg_succ /= count
            avg_inf /= count
            avg_inf /= 2
            avg_order /= count
            writer.writerow([key, count, avg_succ, avg_inf, avg_order])
    writer.writerow([])


def print_label_counts_with_keys(suffix, server, discussions, normalized):
    outcome_labels = {}
    vote_labels = {}
    comment_labels = {}
    keyed_votes = {}
    keyed_outcomes = {}
    keyed_comments = {}
    keyed_sessions = {}

    # Preload for by_year=True
    timestamp_cutoffs = {}
    for y in range(2005,2019):
        code, cutoffs = server.util.get_timestamps_for_year(y)
        timestamp_cutoffs[y] = cutoffs

    for disc_id in discussions:
        latest_year = -1
        latest_timestamp = -1
        code, contrib_ids = server.discussions.get_contributions(disc_id)

        disc_votes = {}
        if disc_id % 1000 == 0:
            print("Processing discussion {}".format(disc_id))
        
        contribs_to_users = {}
        users_to_contribs = {}
        for i, contrib_id in enumerate(contrib_ids):
            code, user = server.util.get_user_id(contrib_id)
            contribs_to_users[contrib_id] = user
            if user not in users_to_contribs.keys():
                users_to_contribs[user] = []
            users_to_contribs[user].append(contrib_id)

        for i, contrib_id in enumerate(contrib_ids):
            first_vote_for_v = False
            if server.util.is_vote(contrib_id):
                code, v = server.votes.get_label(contrib_id, normalized=normalized)
                if v not in disc_votes.keys():
                    disc_votes[v] = 1
                    first_vote_for_v = True
            if True:#first_vote_for_v:
                user_activity = users_to_contribs[contribs_to_users[contrib_id]]
                latest_year, latest_timestamp, vote_labels, keyed_votes = process_votes(server, timestamp_cutoffs, contrib_id, latest_year, i, latest_timestamp, user_activity, vote_labels, keyed_votes)
                latest_year, latest_timestamp, comment_labels, keyed_comments = process_comments(server, timestamp_cutoffs, contrib_id, latest_year, i, latest_timestamp, user_activity, comment_labels, keyed_comments) 

        code, outcome_id = server.discussions.get_outcome_id(disc_id)
        keyed_outcomes = process_outcomes(server, outcome_id, latest_year, outcome_labels, keyed_outcomes)

    output_file = open("cscw_output_{}.csv".format(suffix), "w")
    output_csv = csv.writer(output_file)
    output_summary_map(output_csv, "Outcomes:", outcome_labels)
    output_summary_map(output_csv, "Votes:", vote_labels)
    output_summary_map(output_csv, "Comments:", comment_labels)
    output_summary_map(output_csv, "Keyed Outcomes:", keyed_outcomes)
    output_summary_map(output_csv, "Keyed Votes:", keyed_votes)
    output_summary_map(output_csv, "Keyed Comments:", keyed_comments)

    return outcome_labels, vote_labels, comment_labels



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

if __name__ == "__main__":
    normalized = 2
    config = {
        "extractors": ["TALLY"],
        "normalized": normalized,
        "strict_discussions": True,
        "source": "afd_2019_full_policies.json"
    }

    server = DebateServer(config)
    start = time.time()
    cscw(server, normalized)
    end = time.time()
    print("{} seconds for processing request.".format((end-start)))

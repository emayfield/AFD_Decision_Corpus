import csv

def get_examples(server, normalized=2, vote_pattern=None, cite=None):
    code, discussions = server.discussions.get_all()
    if code == 200:
        for disc_id in discussions:
            code, title = server.discussions.get_title(disc_id)
            code, contribs = server.discussions.get_contributions(disc_id)

            if vote_pattern is not None:
                i = 0
                print(f"Testing vote pattern {vote_pattern}")
                for c in contribs:
                    if i < len(vote_pattern):
                        if server.util.is_vote(c):
                            code, label = server.votes.get_label(c, normalized=normalized)
                            if vote_pattern[i] == label:
                                i += 1
                                print(f"      MATCH: {label}")
                                if i == len(vote_pattern):
                                    print(title)
                print(f"Got to i={i}")
                                
            # Find by citation
            if cite is not None:
                for contrib_id in contribs:
                    if server.util.is_vote(contrib_id):
                        code, cites = server.votes.get_citations(contrib_id)
                        if key in cites:
                            print(title)

def generate_single_profile(server, user_id):
    details = {}
    details["id"]= user_id

    """Produces four possible genders: male, female, unregistered, unknown"""
    code, gender = server.users.get_gender(user_id)
    if code == 200:
        details["gender"] = gender

    code, registered = server.users.is_registered(user_id)
    if code == 200 and not registered:
        details["gender"] = "unregistered"

    """Produces two enfranchised levels: high and low, based on total lifetime edit count."""
    code, edit_count = server.users.get_edit_count(user_id)
    if code == 200:
        details["enfranchised"] = (edit_count is not None and edit_count > 250)

    return details




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


def check_success(server, contribs):
    max_success = 0
    latest_label = ""
    for contrib_id in contribs:
        if server.util.is_vote(contrib_id):
            code, this_success = server.votes.get_success(contrib_id)
            if this_success is not None:
                max_success = max(max_success, this_success)
    return max_success > 0

def cume_shift(server, contribs):
    cume_shift = 0.0
    for contrib_id in contribs:
        shift = 0
        if server.util.is_vote(contrib_id):
            code, shift = server.votes.get_influence(contrib_id)
        if server.util.is_comment(contrib_id):
            code, shift = server.comments.get_influence(contrib_id)
        if shift is not None and shift > 0:
            cume_inf += influence
    return max_success > 0

def summarize_log(filename, key_strings, log):
    rates = {}

    csv_writer = csv.writer(open(f"survival_{filename}.csv", "w"))
    header = ["gender", "enfranchised", "tenure", "positive", "total", "rate"]
    csv_writer.writerow(header)
    for key in log:
        positive = 0
        total = 0
        for event in log[key]:
            if event:
                positive += 1
            total += 1
        rate = (positive/total)

        row_key = key_strings[key]
        row_key.extend([positive, total, rate])
        csv_writer.writerow(row_key)
        rates[key] = rate
    return rates

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
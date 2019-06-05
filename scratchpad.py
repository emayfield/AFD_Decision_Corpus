import time
import csv
import math
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from endpoints.helpers.cache import store, lookup
import operator
import os

def dry_run(server):
#    predict_comment_preferences(server)
#    explore_influences(server)
#    export_influences(server)
#    sanity_test_bert(server)
#    basic_bert(server)
#    measure_discussion_quality(server)
#    influences_by_user(server)
#    corpus_statistics(server)
    accuracy_at_points(server)
    #server.import_corpus("test_corpus.json")
    #running_vote_tallies(server)
    #success_distributions_by_tenure(server)
    #vote_breakdown_by_year(server)
    #user_count_by_tenure(server)
    #participation_breakdown_by_user(server)

def predict_comment_preferences(server):
    code, disc_ids = server.discussions.get_all()

    for disc_id in disc_ids:
        server.instances.post_instance(disc_id, 9999999999)
    code, instance_ids = server.instances.get_all()
    print("Created {} discussion instances.".format(len(instance_ids)))

    vote_counts = []
    all_vector_ids = []
    for i, instance_id in enumerate(instance_ids):
        code, vector_ids = server.vectors.post_comment_task_x(instance_id)
        code, disc_id = server.instances.get_discussion_id(instance_id)
        code, contrib_ids = server.discussions.get_contributions(disc_id)

        for v in vector_ids:
            vote_counts.append(len(contrib_ids))

        if vector_ids is not None:
            all_vector_ids.extend(vector_ids)
    print("{} total instances in corpus.".format(len(all_vector_ids)))
    

    texts = []
    for instance_id in instance_ids:
        code, vector_ids = server.instances.get_vector_ids(instance_id)
        code, contribs = server.instances.get_contribution_ids(instance_id)
        for j, v in enumerate(vector_ids):
            for c in contribs:
                code, contrib_text = server.votes.get_rationale(c)
                code, label = server.votes.get_label(c, normalized = server.config["normalized"])
#                if contrib_text is not None and "\'\'\'Delete\'\'\'" in contrib_text:
#                    print(label)
#                print(contrib_text)
                texts.append(contrib_text)

    code, corpus_id = server.corpora.post_corpus(all_vector_ids)
    code, preds_id = server.prediction.post_prediction(corpus_id)
    print("Posted predictions")

    i = 0

    pred_y = []
    prob_y = []
    actual_y = []
    titles = []

    for instance_id in instance_ids:
        code, vector_ids = server.instances.get_vector_ids(instance_id)
        code, contribs = server.instances.get_contribution_ids(instance_id)

        code, disc_id = server.instances.get_discussion_id(instance_id)
        code, title = server.discussions.get_title(disc_id)
        code, outcome_id = server.discussions.get_outcome_id(disc_id)
        code, label = server.outcomes.get_label(outcome_id, normalized = server.config["normalized"])

        vote_texts = []

        code, contrib_from_disc = server.discussions.get_contributions(disc_id)

        for c in contrib_from_disc:
            if server.util.is_vote(c):
                code, rat = server.votes.get_rationale(c)
                vote_texts.append(rat)

#        print("{} {}".format(len(vector_ids), len(vote_texts)))
        for j, v in enumerate(vector_ids):
            code, pred = server.prediction.get_prediction(preds_id, i)
            code, prob = server.prediction.get_probabilities(preds_id, i)
#            print("Vector {} Pred {} Act {} prob {}".format(v,pred,label,prob))
            pred_y.append(pred)
            prob_y.append(prob)
            actual_y.append(label)
            titles.append(title)
#            if pred != label:
#                print("{} pred {} act {}: [{}]".format(v, pred, label, vote_texts[j]))
            i += 1
        
#    for ix in range(len(pred_y)):
#        if pred_y[ix] != actual_y[ix]:
#            print("{} {}: {}\n----------".format(pred_y[ix], actual_y[ix], texts[ix]))

def explore_influences(server):
    cache_path = open("cachepath","r").read().strip()
    code, disc_ids = server.discussions.get_all()

    map_disc = {}
    map_users = {}

    map_orders = {}



    for disc_id in disc_ids:
        if disc_id % 1000 == 0:
            print("Importing {}".format(disc_id))
        code, contrib_ids = server.discussions.get_contributions(disc_id)
        
        for i, c in enumerate(contrib_ids):
            contrib_code = str(c)[0]
            user = -1
            if contrib_code in ["4","5"]:
                code, cached_inf = lookup(cache_path, ["bert_influence"], c)
                cached_inf = cached_inf.strip()
                if code == 200 and cached_inf is not None and cached_inf != 'None':
                    inf = float(cached_inf)
                    if contrib_code == "4":
                        server.votes.put_influence(c, inf)
                        code, user = server.votes.get_user_id(c)
                    if contrib_code == "5":
                        server.comments.put_influence(c, inf)
                        code, user = server.comments.get_user_id(c)
                    if not disc_id in map_disc.keys():
                        map_disc[disc_id] = []
                    map_disc[disc_id].append(inf)
                    if user != -1:
                        if not user in map_users.keys():
                            map_users[user] = []
                        map_users[user].append(inf)
                    order = "{}".format(i)

                    if order not in map_orders.keys():
                        map_orders[order] = []
                    map_orders[order].append(inf)

                    if contrib_code == "4":
                        code, label = server.votes.get_label(c)
                        order_key = "{} {}".format(i, label)
                        if order_key not in map_orders.keys():
                            map_orders[order_key] = []
                        map_orders[order_key].append(inf)


    user_total = {}
    user_avg = {}
    for user in map_users:
        if len(map_users[user]) >= 50:
            user_total[user] = sum(map_users[user])
            user_avg[user] = user_total[user]/len(map_users[user])
    
    orders_avg = {}
    orders_total = {}
    for order in map_orders:
        orders_total[order] = sum(map_orders[order])
        orders_avg[order] = orders_total[order]/len(map_orders[order])

    ranked_users = list(sorted(user_avg.items(), key=operator.itemgetter(1)))
    ranked_orders = list(sorted(orders_avg.items(), key = operator.itemgetter(1)))

    for o in range(1, 12):
        if str(o) in orders_avg.keys():
            print(orders_avg[str(o)]/2)

    print("---")
    for label in ["Delete", "Keep"]:
        for o in range(1, 12):
            k = "{} {}".format(o, label)
            if k in orders_avg.keys():
                print(orders_avg[k]/2)
        print("---")

    for user_tuple in ranked_users:
        user, total = user_tuple
        code, username = server.users.get_name(user)
        print("User [{}]: Total {} Average {}".format(username, user_total[user], user_avg[user]))
        code, vote_ids = server.votes.get_votes_by_user(user)
        for v in vote_ids:
            code, infl = server.votes.get_influence(v)
            code, text = server.votes.get_rationale(v)
            code, disc = server.votes.get_discussion_id(v)
            code, title = server.discussions.get_title(disc)
            if "Hammer" in username:
                print("{} {} {}: {}".format(title, v, infl, text))
        
def corpus_statistics(server):
    code, disc_ids = server.discussions.get_all()
    out_labels = {} 
    out_totals = 0
    vote_labels = {}
    vote_totals = 0
    for disc_id in disc_ids:
        if disc_id % 1000 == 0:
            print("Measuring {}".format(disc_id))
        code, contrib_ids = server.discussions.get_contributions(disc_id)
        
        out_label = None
        code, outcome_id = server.discussions.get_outcome_id(disc_id)
        if code == 200 and outcome_id is not None:
            code, out_label = server.outcomes.get_label(outcome_id)
            if out_label is not None and out_label not in out_labels.keys():
                out_labels[out_label] = 0
            
        for contrib_id in contrib_ids:
            contrib_code = str(contrib_id)[0]
            if contrib_code == "4":
                code, vote_label = server.votes.get_label(contrib_id)
                if code == 200 and vote_label is not None:
                    if vote_label not in vote_labels.keys():
                        vote_labels[vote_label] = 0
                    vote_labels[vote_label] = vote_labels[vote_label] + 1
                    vote_totals += 1
            
            if contrib_code == "4" or contrib_code == "5":
                if out_label is not None:
                    out_labels[out_label] = out_labels[out_label] + 1
                    out_totals += 1
                    

        

    print("Votes:")
    for v in vote_labels.keys():
        print("{} {} {}".format(v, vote_labels[v], (vote_labels[v]/vote_totals)))
    print("Outcomes:")
    for o in out_labels.keys():
        print("{} {} {}".format(o, out_labels[o], (out_labels[o]/out_totals)))


def export_influences(server):
    cache_path = open("cachepath","r").read().strip()
    generate_influences(server)
    code, discussion_ids = server.discussions.get_all()

    csv_out = open("consensus_stats.csv", "w")
    csv_write = csv.writer(csv_out)
    csv_write.writerow(['disc_id','contrib_id', 'user','label', 'consensus'])
    for disc_id in discussion_ids:
        code, title = server.discussions.get_title(disc_id)
        code, contrib_ids = server.discussions.get_contributions(disc_id)
#        print("Disc [{}] len {}".format(title, len(contrib_ids)))
        influences = []

        for c in contrib_ids:
            contrib_code = str(c)[0]
            inf = -1
            if contrib_code == "4":
                code, label = server.votes.get_label(c)
                code, user_id = server.votes.get_user_id(c)
                code, username = server.users.get_name(user_id)
                code, inf = server.votes.get_influence(c)
            if contrib_code == "5":
                code, user_id = server.comments.get_user_id(c)
                code, username = server.users.get_name(user_id)
                code, inf = server.comments.get_influence(c)
                label = "Comment"

            if inf != -1:
                if c % 1000 == 0:
                    print("Exporting {}".format(c))
                store(cache_path, "bow_influence", c, inf)

        if False:
            for i, c in enumerate(contrib_ids):
                before_inf = 0
                before_count = 0
                after_inf = 0
                after_count = 0
                label = None
                username = None

                contrib_code = str(c)[0]
                if contrib_code == "4":
                    code, label = server.votes.get_label(c)
                    code, user_id = server.votes.get_user_id(c)
                    code, username = server.users.get_name(user_id)
                if contrib_code == "5":
                    code, user_id = server.comments.get_user_id(c)
                    code, username = server.users.get_name(user_id)
                    label = "Comment"

                for j, d in enumerate(contrib_ids):
                    inf = 0
                    contrib_code = str(d)[0]
                    # exclude 3 and 6 here next!
                    if contrib_code == "4":
                        code, inf = server.votes.get_influence(d)
                    if contrib_code == "5":
                        code, inf = server.comments.get_influence(d)
                    if j < i and inf is not None:
                        before_inf += inf
                        before_count += 1
                    elif inf is not None:
                        after_inf += inf
                        after_count += 1
                
                pre = before_inf/before_count if before_count > 0 else 0
                post = after_inf/after_count if after_count > 0 else 0

                consensus = pre-post

                csv_write.writerow([title, c, username, label, consensus])

def measure_discussion_quality(server):
    generate_influences(server)
    code, discussion_ids = server.discussions.get_all()
    csv_out = open("quality_metrics_20k.csv", "w")
    csv_write = csv.writer(csv_out)
    headers = ["DiscID","Title","Overall", "Quantity","Diversity","Conflict","Consensus","Fairness"]
    csv_write.writerow(headers)
    for disc_id in discussion_ids:

        code, title = server.discussions.get_title(disc_id)

        """
        More participants = better
        """
        q = measure_participant_quantity(server, disc_id)

        """
        More diverse participants = better
        """
        d = measure_participant_diversity(server, disc_id)

        """
        More bursty conversations = better
        """
        b = measure_burstiness(server, disc_id)

        """
        More conflict resolution = better
        """
        c1, c2 = measure_participant_conflict_consensus(server, disc_id)


        """
        Less biased administrators = better
        (but only when verdict is in direction of their bias?)
        """
        f = measure_administrator_bias(server, disc_id)

        
        if q > 0:
            out = [disc_id, title, 0, q, d, c1, c2, f]
            csv_write.writerow(out)

def sanity_test_bert(server):
    code, discussion_ids = server.discussions.get_all()
    for disc_id in discussion_ids:
        code, title = server.discussions.get_title(disc_id)
        code, contrib_ids = server.discussions.get_contributions(disc_id)
        print("*********DISC {} TITLE [{}] CONTRIBS {}*********".format(disc_id, title, len(contrib_ids)))
        measure_content_diversity(server, disc_id)


def measure_content_diversity(server, disc_id):
    code, contrib_ids = server.discussions.get_contributions(disc_id)
    vectors = []
    for c in contrib_ids:
        cv = server.extractors[0].single_contrib_features(c)
        if cv is not None:
            for d in contrib_ids:
                dv = server.extractors[0].single_contrib_features(d)
                if dv is not None:

                    c_code = str(c)[0]
                    d_code = str(d)[0]
                    c_text = ""
                    d_text = ""
                    if c_code == "4":
                        code, c_text = server.votes.get_rationale(c)
                    if c_code == "5":
                        code, c_text = server.comments.get_text(c)
                    if c_code == "6":
                        code, c_text = server.nominations.get_text(c)
                    if d_code == "4":
                        code, d_text = server.votes.get_rationale(d)
                    if d_code == "5":
                        code, d_text = server.comments.get_text(d)
                    if d_code == "6":
                        code, d_text = server.nominations.get_text(d)

                    np_cv = np.array(cv).reshape(1, -1)
                    np_dv = np.array(dv).reshape(1, -1)
                    sim = cosine_similarity(np_cv, np_dv)
                    if 0.96 < sim < 0.99:
                        print("---COMPARE {} TO {}: {}---".format(c, d, sim))
                        print(c_text)
                        print("---")
                        print(d_text)


def measure_burstiness(server, disc_id):
    code, contrib_ids = server.discussions.get_contributions(disc_id)
    wait_times = []
    last_timestamp = None
    for contrib_id in contrib_ids:
        contrib_code = str(contrib_id)[0]
        timestamp = None
        if(contrib_code == "4"):
            code, timestamp = server.votes.get_timestamp(contrib_id)
        if(contrib_code == "5"):
            code, timestamp = server.comments.get_timestamp(contrib_id)
        if(contrib_code == "6"):
            code, timestamp = server.nominations.get_timestamp(contrib_id)
        
        if last_timestamp is not None and timestamp is not None:
            wait_times.append(timestamp - last_timestamp)
        
        last_timestamp = timestamp
    sd = np.std(wait_times)
    u = np.mean(wait_times)
    if u != 0:
        return sd/u
    else:
        return 0

def measure_participant_quantity(server, disc_id):
    code, contrib_ids = server.discussions.get_contributions(disc_id)
    participant_ids = {}
    for contrib_id in contrib_ids:
        contrib_code = str(contrib_id)[0]
        user_id = None
        if(contrib_code == "4"):
            code, user_id = server.votes.get_user_id(contrib_id)
        if(contrib_code == "5"):
            code, user_id = server.comments.get_user_id(contrib_id)
        if(contrib_code == "6"):
            code, user_id = server.nominations.get_user_id(contrib_id)
        if user_id is not None:
            participant_ids[user_id] = 1
    quantity = len(participant_ids.keys())
    if quantity > 0:
        quantity = math.log(quantity, 10)
    return quantity

def measure_participant_diversity(server, disc_id):
    code, contrib_ids = server.discussions.get_contributions(disc_id)
    participant_ids = {}
    for contrib_id in contrib_ids:
        contrib_code = str(contrib_id)[0]
        user_id = -1
        if(contrib_code == "4"):
            code, user_id = server.votes.get_user_id(contrib_id)
        if(contrib_code == "5"):
            code, user_id = server.comments.get_user_id(contrib_id)
        if(contrib_code == "6"):
            code, user_id = server.nominations.get_user_id(contrib_id)
        if user_id not in participant_ids.keys():
            code, tenure = server.users.get_tenure_at_contribution(user_id, contrib_id)
            if code == 200:
                participant_ids[user_id] = tenure
    
    tenures = [participant_ids[u] for u in participant_ids.keys()]
    sd = np.std(tenures)
    u = np.mean(tenures)
    if u != 0:
        return sd/u
    else:
        return 0


def measure_participant_conflict_consensus(server, disc_id):
    code, contrib_ids = server.discussions.get_contributions(disc_id)
    vote_ids = {}
    for contrib_id in contrib_ids:
        contrib_code = str(contrib_id)[0]
        if(contrib_code == "4"):
            code, influence = server.votes.get_influence(contrib_id)
            if influence is not None:
                vote_ids[contrib_id] = abs(influence)
    influences = [vote_ids[x] for x in vote_ids.keys()]
    conflict = 0 if len(influences) == 0 else np.sum(influences)
    consensus = 0 if len(influences) == 0 else 1/np.std(influences)
    if str(consensus) == "inf":
        print(influences)
    return conflict, consensus


def measure_administrator_bias(server, disc_id):
    return 0

def generate_influences(server):
    code, disc_ids = server.discussions.get_all()

    for disc_id in disc_ids:
        server.instances.post_instance(disc_id, 9999999999)
    code, instance_ids = server.instances.get_all()
    print("Created {} discussion instances.".format(len(instance_ids)))
    code, feature_names = server.vectors.get_feature_names()
    
    vote_counts = []
    all_vector_ids = []
    for i, instance_id in enumerate(instance_ids):
        code, vector_ids = server.vectors.post_all_x(instance_id)
        code, disc_id = server.instances.get_discussion_id(instance_id)
        code, contrib_ids = server.discussions.get_contributions(disc_id)

        for v in vector_ids:
            code, vector = server.vectors.get_by_id(v)
            vote_counts.append(len(contrib_ids))

        if vector_ids is not None:
            all_vector_ids.extend(vector_ids)
    print("{} total instances in corpus.".format(len(all_vector_ids)))
    
    code, corpus_id = server.corpora.post_corpus(all_vector_ids)
    code, preds_id = server.prediction.post_prediction(corpus_id)
    print("Posted predictions")
    code, vector_ids = server.prediction.put_influences(preds_id)
    print("Posted influences")


def influences_by_user(server):
    generate_influences(server)
    code, user_ids = server.users.get_all()
    all_users = {}
    for user_id in user_ids:
        user_influences = []
        user_votes = {}
        user_discussions = {}
        code, name = server.users.get_name(user_id)
#        print("{}:".format(name))

        code, contrib_ids = server.users.get_contributions(user_id)
        for c in contrib_ids:
            contrib_code = str(c)[0]
            if contrib_code == "4":
                code, influence = server.votes.get_influence(c)
                code, label = server.votes.get_label(c)
                code, discussion_id = server.votes.get_discussion_id(c)
                code, title = server.discussions.get_title(discussion_id)
#                print("      Influence {} from voting {} on discussion [{}]".format(influence, label, title))
                if code == 200 and influence is not None:
                    user_influences.append(influence)
                    if label not in user_votes.keys():
                        user_votes[label] = []
                    user_votes[label].append(influence)
                    if discussion_id not in user_discussions.keys():
                        user_discussions[discussion_id] = []
                    user_discussions[discussion_id].append(influence)
                else:
                    user_influences.append(0)
        
        all_users[user_id] = {
            "influences": user_influences,
            "votes": user_votes,
            "discussions": user_discussions
        }
    
    users_out = open("user_impacts.csv","w")
    users_csv = csv.writer(users_out)
    headers = [
        "user",
        "sum",
        "avg",
        "tot",
        "avg-d",
        "sum-d",
        "tot-d",
        "avg-k",
        "sum-k",
        "tot-k",
        "unq-disc"
    ]
    users_csv.writerow(headers)
    for user_id in all_users.keys():
        code, name = server.users.get_name(user_id)
        sum = 0
        unq = 0
        for inf in all_users[user_id]["influences"]:
            sum += inf
            unq += 1
        avg = 0
        if unq != 0:
            avg = sum/unq
        row = [name,sum,avg,unq]

        for l in ["Delete","Keep"]:
            sum = 0
            unq = 0
            if l in all_users[user_id]["votes"].keys():
                for inf in all_users[user_id]["votes"][l]:
                    sum += inf
                    unq += 1
            avg = 0
            if unq != 0:
                avg = sum/unq
            row.extend([avg,sum,unq])
        row.extend([len(all_users[user_id]["discussions"].keys())])
        users_csv.writerow(row)
        

def accuracy_at_points(server):
    code, disc_ids = server.discussions.get_all()

    for disc_id in disc_ids:
        if disc_id % 10000 == 0:
            print("Posting {}".format(disc_id))
        server.instances.post_instance(disc_id, 9999999999)
    
    code, instance_ids = server.instances.get_all()
    print("{} inst found".format(len(instance_ids)))
    code, feature_names = server.vectors.get_feature_names()
    

    vote_counts = []
    place_in_disc = []
    all_vector_ids = []

    for i, instance_id in enumerate(instance_ids):
        code, contrib_ids = server.instances.get_contribution_ids(instance_id)
        if len(contrib_ids) > 0:
            code, vector_ids = server.vectors.post_all_x(instance_id)

            code, disc_id = server.instances.get_discussion_id(instance_id)
            code, title = server.discussions.get_title(disc_id)

    #        print(",".join([str(x) for x in contrib_ids]))
    #        print("{} vectors for [{}]".format(len(vector_ids), title))
            for j, v in enumerate(vector_ids):
                code, vector = server.vectors.get_by_id(v)
                vote_counts.append(len(contrib_ids))
                at_point = round(j/len(vector_ids),1)
                place_in_disc.append(at_point)
    #            print("Appending {} {}".format(len(contrib_ids), j))
    #            vote_counts.append(vector.x["Total Votes"])

            if vector_ids is not None:
                all_vector_ids.extend(vector_ids)
    print("{} total instances in corpus.".format(len(all_vector_ids)))
    
    code, corpus_id = server.corpora.post_corpus(all_vector_ids)
    code, preds_id = server.prediction.post_prediction(corpus_id)


    i = 0
    pred_y = []
    prob_y = []
    actual_y = []
    titles = []

    labels = ["Delete", "Keep", "Merge", "Other", "Redirect"]
    for instance_id in instance_ids:
        code, vector_ids = server.instances.get_vector_ids(instance_id)
        code, contribs = server.instances.get_contribution_ids(instance_id)

        code, disc_id = server.instances.get_discussion_id(instance_id)
        code, title = server.discussions.get_title(disc_id)
        code, outcome_id = server.discussions.get_outcome_id(disc_id)
        code, label = server.outcomes.get_label(outcome_id)


        for j, v in enumerate(vector_ids):
            code, pred = server.prediction.get_prediction(preds_id, i)
            code, prob = server.prediction.get_probabilities(preds_id, i)
#            print("Vector {} Pred {} Act {} prob {}".format(v,pred,label,prob))
            pred_y.append(pred)
            prob_y.append(prob)
            actual_y.append(label)
            titles.append(title)

#            if pred != label:
#                print("{} pred {} act {}: [{}]".format(disc_id, pred, label, title))
            i += 1

    results = {}

    for i, pred in enumerate(pred_y):
        num_contribs = vote_counts[i] - 2
        key_A = num_contribs
        if num_contribs <= 5:
            key_A = "<=5"
        if 5 < num_contribs <= 10:
            key_A = "6-10"
        if 10 < num_contribs:
            key_A = ">10"

        key_B = place_in_disc[i]

#        if 5 < place_in_disc[i] <= 10:
#            key_B = "6-10"
#        if 10 < place_in_disc[i]:
#            key_B = ">10"

        key_C = pred_y[i]

        sort_key = "{} {}".format(key_A, key_B)

        act_transf = actual_y[i]
        if act_transf in ["Merge", "Redirect"]:
            act_transf = "Delete"
        if act_transf in ["Other"]:
            act_transf = "Keep"
        acc = (pred == act_transf)
        if sort_key not in results.keys():
            results[sort_key] = []

        results[sort_key].append(acc)
    
    for key in results.keys():
        matches = 0
        for v in results[key]:
            if v:
                matches += 1
        total = len(results[key])
        acc_val = matches/total if total > 0 else 0
        print("[{}]: {}/{} = {}".format(key, matches, total, acc_val))

    if False:
        for i in range(0,30):
            numer = 0
            denom = 0
            for j, p in enumerate(pred_y):
                vote_count = vote_counts[j]
                if vote_count==i:
                    denom += 1
                a = actual_y[j]
                if p == a and vote_count==i:
                    numer += 1
            
            all_numer += numer
            all_denom += denom
    #        print("{}".format((all_numer/all_denom)))
            if denom > 0:
                print("{}".format((numer/denom)))
            else:
                print("NAN")
    #        print("i={}: {}/{} = {}".format(i,numer,denom,(numer/denom)))
    print("prediction task {} complete".format(preds_id)) 

    print("starting influences")
    code, vector_ids = server.prediction.put_influences(preds_id)
    print("ending influences")
    preserved_influences = {}
    code, all_nominations = server.nominations.get_all()
    code, all_comments = server.comments.get_all()
    code, all_votes = server.votes.get_all()

    for c in all_comments:
        code, inf = server.comments.get_influence(c)
        preserved_influences[c] = inf
    for v in all_votes:
        code, inf = server.votes.get_influence(v)
        preserved_influences[v] = inf
    
    i = 0
    found_open = False
    filename = None
    while not found_open:
        i += 1
        filename = "cached_influences_Wednesday_offset_{}.csv".format(i)
        found_open = not os.path.isfile(filename)
    print("opening {}".format(filename))
    cached_influences = open(filename, "w")
    csv_out = csv.writer(cached_influences)
    for key in preserved_influences.keys():
        csv_out.writerow([key, preserved_influences[key]])




def running_vote_tallies(server):
    code, disc_ids = server.discussions.get_all()
    for disc_id in disc_ids:
        code, title = server.discussions.get_title(disc_id)
        print("Running tallies for discussion [{}]".format(title))
        code, contrib_ids = server.discussions.get_contributions(disc_id)
        for c in contrib_ids:
            print(c)
        for contrib_id in contrib_ids:
            timestamp = -1
            contrib_code = str(contrib_id)[0]
            contrib_type = ""

            if contrib_code == "4":
                code, timestamp = server.votes.get_timestamp(contrib_id)
                contrib_type = "vote"
            if contrib_code == "5":
                code, timestamp = server.comments.get_timestamp(contrib_id)
                code, raw_text = server.comments.get_text(contrib_id)
                contrib_type = "comment"
            if contrib_code == "6":
                code, timestamp = server.nominations.get_timestamp(contrib_id)
                contrib_type = "nomination"
            if timestamp != -1:
                code, contribs_at_snapshot = server.discussions.get_contributions_at_time(disc_id, timestamp)
                code, vote_tally = server.votes.get_vote_tally(contribs_at_snapshot)
                code, raw = server.votes.get_label(contrib_id, normalized=0)
                user = "???"
                user_id = -1
                if contrib_code == "4":
                    code, user_id = server.votes.get_user_id(contrib_id)
                if contrib_code == "5":
                    code, user_id = server.comments.get_user_id(contrib_id)
                if contrib_code == "6":
                    code, user_id = server.nominations.get_user_id(contrib_id)
                if code == 200 and user_id != -1:
                    code, user = server.users.get_name(user_id)
                print("------")
                print("              Snapshot vote tally prior:")
                for l in vote_tally.keys():
                    print("                        {}:{}".format(l, vote_tally[l]))

                print("        New  {} at time {} by {}! [{}]".format(contrib_type, timestamp, user, raw))
        code, outcome_id = server.discussions.get_outcome_id(disc_id)
        code, outcome = server.outcomes.get_label(outcome_id)
        code, admin_id = server.outcomes.get_user_id(outcome_id)
        code, admin_name = server.users.get_name(admin_id)
        print("=========")
        print("Outcome by [{}]: {}".format(admin_name, outcome))
        print("*************************************")

"""
Can look at votes (mode = "V") or nominations ("N").
"""
def success_distributions_by_tenure(server, mode = "V", count_unique_users=False):
    ids = []
    if mode == "N":
        code, ids = server.nominations.get_all()
    if mode == "V":
        code, ids = server.votes.get_all()
    success_rates = {}
    max_tenure = 0
    yes = 0
    no = 0
    start = time.time()
    unique_in_bracket = {}
    for i in ids:
        user_id = -1
        if mode == "N":
            code, user_id = server.nominations.get_user_id(i)
        if mode == "V":
            code, user_id = server.votes.get_user_id(i)
        code, tenure = server.users.get_tenure_at_contribution(user_id, i)
        
        if code != 200:
            no += 1
        else:
            yes += 1
            if count_unique_users:
                for cuts in range(0,20):
                    bottom_cutoff = 2**(cuts)
                    top_cutoff = 2**(cuts+1)
                    if bottom_cutoff <= tenure < top_cutoff:
                        if cuts not in unique_in_bracket.keys():
                            unique_in_bracket[cuts] = {}
                        if user_id not in unique_in_bracket[cuts].keys():
                            unique_in_bracket[cuts][user_id] = 1
                        else:
                            unique_in_bracket[cuts][user_id] = unique_in_bracket[cuts][user_id] + 1

            code, success = server.analysis.get_success_status(i)
            if tenure not in success_rates.keys():
                success_rates[tenure] = {}
            if success in success_rates[tenure].keys():
                success_rates[tenure][success] = success_rates[tenure][success] + 1
            else:
                success_rates[tenure][success] = 1
            max_tenure = max(max_tenure, tenure)
        if yes%1000==0:
            end = time.time()
            print("{} seconds for {} yes, {} no".format((end-start), yes, no))
            start = end

    print("{} load, {} fail".format(yes,no))
    
    noms_out = open("{}_tenure_distro.csv".format(mode), "w")
    csv_out = csv.writer(noms_out)
    headers = ["min","max","win#","lose#","unk#","win%","lose%","unk%"]
    csv_out.writerow(headers)
    for i in range(0,20):
        bottom_cutoff = 2**(i)
        top_cutoff = 2**(i+1)
        print("Range {} to {}".format(bottom_cutoff, (top_cutoff-1)))
        total_tally = {}
        for j in range(bottom_cutoff, top_cutoff):
            if j in success_rates.keys():
                code, total_tally = server.math.get_combined_tally(total_tally, success_rates[j])
        row = [bottom_cutoff,(top_cutoff-1)]
        for key in ["Win", "Lose", "Unclear"]:
            mode_key = "{} {}".format("Nom" if mode == "N" else "Vote", key)
            val = "N/A"
            if mode_key in total_tally.keys():
                val = success_rates[i][mode_key]
            row.append(val)
        code, success_norm = server.math.get_normalized_tally(total_tally)
        for key in ["Win", "Lose", "Unclear"]:
            mode_key = "{} {}".format("Nom" if mode == "N" else "Vote", key)
            val = "N/A"
            if mode_key in success_norm.keys():
                val = success_norm[mode_key]
            row.append(val)
        csv_out.writerow(row)
    if count_unique_users:
        noms_out = open("{}_tenure_user_counts.csv".format(mode), "w")
        csv_out = csv.writer(noms_out)
        headers = ["bracket","user_id","count"]
        csv_out.writerow(headers)
        for cut in unique_in_bracket.keys():
            for user_id in unique_in_bracket[cut].keys():
                row = [cut, user_id, unique_in_bracket[cut][user_id]]
                csv_out.writerow(row)


def vote_breakdown_by_year(server):
    for year in range(2005,2019):
        code, times = server.time.get_timestamps_for_year(year)
        code, votes = server.votes.get_votes_by_timestamps(start=times[0], end=times[1])
        code, comments = server.comments.get_comments_by_timestamps(start=times[0], end=times[1])
        print("Year {}: {} votes and {} comments".format(year, len(votes), len(comments)))

def user_count_by_tenure(server):
    for i in range(0,15):
        bottom_cutoff = 2**(i)
        top_cutoff = 2**(i+1)
        code, cohort = server.users.get_users_by_tenure(min=bottom_cutoff, max=top_cutoff)
        if code == 200:
            print("Range {}-{}: {} users".format(bottom_cutoff, (top_cutoff-1), len(cohort)))

def participation_breakdown_by_user(server):
    for user_id in server.users.get_all()[1]:
        print(user_id)
        code, breakdown = server.users.get_participation_breakdown(user_id)
        print("  Breakdown:")
        for k in breakdown:
            print("B    {}:{}".format(k,breakdown[k]))
        code, contrib_ids = server.users.get_contributions(user_id)
        counts = {}
        for contrib_id in contrib_ids:
            code, success = server.analysis.get_success_status(contrib_id)
            if success in counts.keys():
                counts[success] = counts[success] + 1
            else:
                counts[success] = 1
        print("  Counts:")
        for k in counts:
            print("C    {}:{}".format(k,counts[k]))
        code, norm_counts = server.math.get_normalized_tally(counts)
        print("  Distribution:")
        for k in norm_counts:
            print("D    {}:{}".format(k,norm_counts[k]))



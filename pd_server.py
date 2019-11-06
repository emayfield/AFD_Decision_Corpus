import time, os
import pandas as pd 

def import_corpus():
    router = {}
    for filename in ["discussions_df.csv", "users_df.csv", "outcomes_df.csv", "votes_df.csv", "comments_df.csv", "nominations_df.csv", "citations_df.csv", "citations_master.csv"]:
        now = time.time()
        path = os.path.join("afd1.1", filename)
        exists = os.path.exists(path)
        if exists:
            df = pd.read_csv(path)
            end = time.time()
            print(f"{(end-now):.3f} seconds to load {filename}")
            router[filename.replace(".csv", "")] = df

    start = time.time()
    router["contribs_df"] = contribs(router)
    end = time.time()
    print(f"{(end-start):.3f} seconds to build sorted contributions list.")

    for k in router:
        print(f"{k}: {router[k].shape}")
    return router


def contribs(router):
    subset_columns = ["user_id", "contrib_id", "timestamp", "contrib_type"]

    votes_df = router["votes_df"]
    v = votes_df.loc[:, ["user_id", "vote_id", "timestamp"]]
    v["contrib_type"] = "vote"
    v.columns = subset_columns

    nominations_df = router["nominations_df"]
    n = nominations_df.loc[:, ["user_id", "nomination_id", "timestamp"]]
    n["contrib_type"] = "nomination"
    n.columns = subset_columns

    comments_df = router["comments_df"]
    c = comments_df.loc[:, ["user_id", "comment_id", "timestamp"]]
    c["contrib_type"] = "comment"
    c.columns = subset_columns

    contribs_df = v.append(c).append(n).sort_values(by="timestamp")
    return contribs_df

def calc_gender_stats(router):
    c = router["contribs_df"]
    print(c.columns)
    for ctype in ["vote", "comment", "nomination"]:
        print(f"--------------------\n{ctype}\n--------------------")
        count_contribs = c.loc[c.contrib_type==ctype].groupby("user_id").size()
        count_contribs = count_contribs.rename("num_contribs")
        user_merge = router["users_df"].join(count_contribs, on="user_id", how="left")
        gender_avg = user_merge.groupby("gender").mean()["num_contribs"]
        print(gender_avg)

if __name__ == "__main__":
    router = import_corpus()
    calc_gender_stats(router)

from endpoints.data.vote import Vote
from tests.fixtures import basic_server, learning_server

import numpy as np

def test_get_all_votes(basic_server):
    code, all = basic_server.votes.get_all()
    assert code == 200
    assert len(all) >= 3

def test_get_one_vote(basic_server):
    code, all = basic_server.votes.get_all()
    assert code == 200
    for key in all:
        code, one = basic_server.votes.get_by_id(key)
        assert code == 200
        assert type(one) is Vote
    code, broken_link = basic_server.votes.get_by_id(-1)
    assert code == 404
    assert broken_link is None

def test_votes_have_labels(basic_server):
    code, all = basic_server.votes.get_all()
    assert code == 200
    for key in all:
        # Test direct access
        code, one = basic_server.votes.get_by_id(key)
        assert code == 200
        assert type(one.label) is str
        assert len(one.label) > 0
        # Test function access.
        code, label = basic_server.votes.get_label(key, normalized=2)
        assert type(label) is str
        assert len(label) > 0
        assert label in ["Keep", "Delete", "Merge", "Redirect", "Other"]

def test_votes_have_users(basic_server):
    code, all = basic_server.votes.get_all()
    assert code == 200
    for key in all:
        code, one = basic_server.votes.get_user_id(key)
        assert code == 200
        assert type(one) is int
        code, user = basic_server.users.get_by_id(one)
        assert code == 200
    
def test_vote_labels_are_normalized(basic_server):
    code, all = basic_server.votes.get_all()
    assert code == 200
    at_least_one_raw_label_differs = False
    at_least_one_semi_norm_label_differs = False
    at_least_one_raw_label_is_a_mess = False
    for key in all:
        code, raw_label = basic_server.votes.get_label(key, normalized = 0)
        code, semi_norm_label = basic_server.votes.get_label(key, normalized = 1)
        code, norm_label = basic_server.votes.get_label(key, normalized = 2)
        # this test used to check a default behavior but now normalized is a required param.
        if raw_label not in ["Keep", "Delete", "Merge", "Redirect", "Other"]:
            at_least_one_raw_label_differs = True
        if semi_norm_label not in ["Keep", "Delete", "Merge", "Redirect", "Other"]:
            at_least_one_semi_norm_label_differs = True
        if raw_label != raw_label.lower():
            at_least_one_raw_label_is_a_mess = True
    assert at_least_one_raw_label_differs
    assert at_least_one_semi_norm_label_differs
    assert at_least_one_raw_label_is_a_mess

def test_votes_have_rationales(basic_server):
    code, all = basic_server.votes.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, rationale = basic_server.votes.get_rationale(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(rationale) is str
        elif code == 404:
            assert rationale is None

def test_votes_have_discussion_ids(basic_server):
    code, all = basic_server.votes.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, disc_id = basic_server.votes.get_discussion_id(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(disc_id) is int
            disc_id_str = str(disc_id)
            assert disc_id_str[0] == "1"
        elif code == 404:
            assert disc_id is None

def test_votes_have_timestamps(basic_server):
    code, all = basic_server.votes.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, timestamp = basic_server.votes.get_timestamp(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(timestamp) is int
        elif code == 404:
            assert timestamp is None

def test_get_votes_by_discussion(basic_server):
    code, discussion_ids = basic_server.discussions.get_all()
    assert code == 200
    code, all_vote_ids = basic_server.votes.get_all()
    assert code == 200
    for disc_id in discussion_ids:
        code, vote_ids = basic_server.votes.get_votes_by_discussion(disc_id)
        assert code == 200
        assert type(vote_ids) is list
        for vote_id in vote_ids:
            assert type(vote_id) is int
            assert vote_id in all_vote_ids

def test_get_votes_by_user(basic_server):
    code, user_ids = basic_server.users.get_all()
    assert code == 200
    code, all_vote_ids = basic_server.votes.get_all()
    assert code == 200
    for user_id in user_ids:
        code, vote_ids = basic_server.votes.get_votes_by_user(user_id)
        assert code == 200
        assert type(vote_ids) is list
        for vote_id in vote_ids:
            assert type(vote_id) is int
            assert vote_id in all_vote_ids

def test_get_vote_tally_by_discussion(basic_server):
    code, discussion_ids = basic_server.discussions.get_all()
    assert code == 200
    for disc_id in discussion_ids:
        code, vote_tally = basic_server.votes.get_vote_tally_by_discussion(disc_id, normalized=2)
        assert code == 200
        assert vote_tally is not None
        assert type(vote_tally) is dict

        total_vote_count = 0
        for label in vote_tally.keys():
            count = vote_tally[label]
            assert type(count) is int
            assert count > 0
            total_vote_count += count

        code, all_votes = basic_server.votes.get_all()
        assert code == 200
        matching_votes = list(filter(lambda x: basic_server.votes.get_by_id(x)[1].discussion_id == disc_id, all_votes))
        assert total_vote_count == len(matching_votes)
        
def test_get_vote_tally_by_user(basic_server):
    code, user_ids = basic_server.users.get_all()
    assert code == 200
    for user_id in user_ids:
        code, vote_tally = basic_server.votes.get_vote_tally_by_user(user_id, normalized=2)
        assert code == 200
        assert vote_tally is not None
        assert type(vote_tally) is dict

        total_vote_count = 0
        for label in vote_tally.keys():
            count = vote_tally[label]
            assert type(count) is int
            assert count > 0
            total_vote_count += count

        code, all_votes = basic_server.votes.get_all()
        assert code == 200
        matching_votes = list(filter(lambda x: basic_server.votes.get_by_id(x)[1].user_id == user_id, all_votes))
        assert total_vote_count == len(matching_votes)
        
def test_get_votes_by_timestamps(basic_server):
    code, vote_ids = basic_server.votes.get_all()
    assert code == 200
    code, all_vote_ids = basic_server.votes.get_votes_by_timestamps()
    assert code == 200
    assert len(all_vote_ids) == len(vote_ids)

    active_timestamps = sorted([basic_server.votes.get_by_id(v)[1].timestamp for v in vote_ids])
    earliest = active_timestamps[0]
    latest = active_timestamps[-1]
    code, filtered_vote_ids = basic_server.votes.get_votes_by_timestamps(end=latest-1)
    assert len(filtered_vote_ids) == len(vote_ids) - 1
    code, filtered_vote_ids = basic_server.votes.get_votes_by_timestamps(start=earliest+1)
    assert len(filtered_vote_ids) == len(vote_ids) - 1
    code, filtered_vote_ids = basic_server.votes.get_votes_by_timestamps(start=earliest+1, end = latest-1)
    assert len(filtered_vote_ids) == len(vote_ids) - 2
    code, filtered_vote_ids = basic_server.votes.get_votes_by_timestamps(start=latest+1)
    assert len(filtered_vote_ids) == 0
    
def test_influence(basic_server):
    code, all = basic_server.votes.get_all()
    for key in all:
        code, influence = basic_server.votes.get_influence(key)
        assert code == 404
        code, vote_id = basic_server.votes.put_influence(key, np.float64(0.2))
        assert code == 200
        assert vote_id == key
        code, influence = basic_server.votes.get_influence(key)
        assert code == 200
        assert type(influence) == np.float64
        assert influence > 0
        

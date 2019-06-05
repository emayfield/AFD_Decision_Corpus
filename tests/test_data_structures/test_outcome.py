import pytest
from tests.fixtures import basic_server
from endpoints.data.outcome import Outcome


def test_get_all_outcomes(basic_server):
    code, all = basic_server.outcomes.get_all()
    assert code == 200
    assert len(all) >= 3

def test_get_one_outcome(basic_server):
    code, all = basic_server.outcomes.get_all()
    assert code == 200
    for key in all:
        code, one = basic_server.outcomes.get_by_id(key)
        assert code == 200
        assert type(one) is Outcome
    code, broken_link = basic_server.outcomes.get_by_id(-1)
    assert code == 404
    assert broken_link is None

def test_outcomes_have_labels(basic_server):
    code, all = basic_server.outcomes.get_all()
    assert code == 200
    for key in all:
        # Test direct access
        code, one = basic_server.outcomes.get_by_id(key)
        assert code == 200
        assert type(one.label) is str
        assert key > 0 and len(one.label) > 0
        # Test function access.
        code, label = basic_server.outcomes.get_label(key, normalized=2)
        assert type(label) is str
        assert len(label) > 0
        assert label in ["Keep", "Delete", "Merge","Redirect", "Other"]

def test_outcomes_have_raw_labels(basic_server):
    code, all = basic_server.outcomes.get_all()
    assert code == 200
    at_least_one_non_exact = False
    for key in all:
        # Test direct access
        code, one = basic_server.outcomes.get_by_id(key)
        assert code == 200
        assert type(one.raw_label) is str
        # Test function access.
        code, label = basic_server.outcomes.get_label(key, normalized=2)
        code, raw_label = basic_server.outcomes.get_label(key, normalized=1)
        assert type(label) is str
        if raw_label != label and raw_label not in ["Keep", "Delete", "Merge","Redirect", "Other"]:
            at_least_one_non_exact = True
    assert at_least_one_non_exact


def test_outcome_labels_are_normalized(basic_server):
    code, all = basic_server.outcomes.get_all()
    assert code == 200
    at_least_one_raw_label_differs = False
    at_least_one_semi_norm_label_differs = False
    at_least_one_raw_label_is_a_mess = False
    for key in all:
        code, raw_label = basic_server.outcomes.get_label(key, normalized = 0)
        code, semi_norm_label = basic_server.outcomes.get_label(key, normalized = 1)
        code, norm_label = basic_server.outcomes.get_label(key, normalized = 2)
        # we used to test a default behavior in the past, but now require the normalized param.
        if raw_label not in ["Keep", "Delete", "Merge","Redirect", "Other"]:
            at_least_one_raw_label_differs = True
        if semi_norm_label not in ["Keep", "Delete", "Merge","Redirect", "Other"]:
            at_least_one_semi_norm_label_differs = True
        if raw_label != raw_label.lower():
            at_least_one_raw_label_is_a_mess = True
    assert at_least_one_raw_label_differs
    assert at_least_one_semi_norm_label_differs
    assert at_least_one_raw_label_is_a_mess

def test_outcomes_have_rationales(basic_server):
    code, all = basic_server.outcomes.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, rationale = basic_server.outcomes.get_rationale(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(rationale) is str
        elif code == 404:
            assert rationale is None

def test_outcomes_have_timestamps(basic_server):
    code, all = basic_server.outcomes.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, timestamp = basic_server.outcomes.get_timestamp(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(timestamp) is int
        elif code == 404:
            assert timestamp is None

def test_get_user_id(basic_server):
    code, all = basic_server.outcomes.get_all()
    assert code == 200
    for key in all:
        code, user_id = basic_server.outcomes.get_user_id(key)
        assert code == 200
        assert type(user_id) is int
        code, retrieve = basic_server.users.get_name(user_id)
        assert code == 200
        assert type(retrieve) == str
        assert len(retrieve) > 0

def test_get_outcomes_by_timestamps(basic_server):
    code, outcome_ids = basic_server.outcomes.get_all()
    assert code == 200
    code, all_outcome_ids = basic_server.outcomes.get_outcomes_by_timestamps()
    assert code == 200
    assert len(all_outcome_ids) == len(outcome_ids)

    active_timestamps = sorted([basic_server.outcomes.get_by_id(o)[1].timestamp for o in outcome_ids])
    earliest = active_timestamps[0]
    latest = active_timestamps[-1]
    code, filtered_outcome_ids = basic_server.outcomes.get_outcomes_by_timestamps(end=latest-1)
    assert len(filtered_outcome_ids) == len(outcome_ids) - 1
    code, filtered_outcome_ids = basic_server.outcomes.get_outcomes_by_timestamps(start=earliest+1)
    assert len(filtered_outcome_ids) == len(outcome_ids) - 1
    code, filtered_outcome_ids = basic_server.outcomes.get_outcomes_by_timestamps(start=earliest+1, end = latest-1)
    assert len(filtered_outcome_ids) == len(outcome_ids) - 2
    code, filtered_outcome_ids = basic_server.outcomes.get_outcomes_by_timestamps(start=latest+1)
    assert len(filtered_outcome_ids) == 0
    
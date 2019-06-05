
import pytest
from tests.fixtures import basic_server

def test_normalized_tally(basic_server):
    code, all = basic_server.votes.get_all()
    assert code == 200
    code, tally = basic_server.votes.get_vote_tally(all, normalized=2)
    assert code == 200
    assert type(tally) is dict
    for k in tally.keys():
        assert type(tally[k]) is int
    code, norm_tally = basic_server.math.get_normalized_tally(tally)
    assert code == 200
    total_probability = 0.0
    assert type(norm_tally) is dict
    for k in norm_tally.keys():
        assert type(norm_tally[k]) is float
        total_probability += norm_tally[k]
    assert 1-total_probability < 0.00001

def test_combined_tally(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    for key in all:
        code, breakdown = basic_server.users.get_participation_breakdown(key)
        assert code == 200
        assert type(breakdown) is dict
        code, doubled = basic_server.math.get_combined_tally(breakdown, breakdown)
        assert code == 200
        assert type(doubled) is dict
        for d in doubled:
            assert d in breakdown.keys()
            assert doubled[d] == 2*breakdown[d]
        doubled["nonexistent"] = 1
        code, tripled = basic_server.math.get_combined_tally(breakdown, doubled)
        assert code == 200
        for t in tripled.keys():
            if t == "nonexistent":
                assert tripled[t] == 1
            else:
                assert t in doubled.keys()
                assert t in breakdown.keys()
                assert tripled[t] == 3*breakdown[t]
        code, normed_breakdown = basic_server.math.get_normalized_tally(breakdown)
        assert code == 200
        code, normed_triples = basic_server.math.get_normalized_tally(tripled)
        code, sums_to_two = basic_server.math.get_combined_tally(normed_breakdown, normed_triples)
        assert code == 200
        sum = 0
        for k in sums_to_two.keys():
            sum += sums_to_two[k]
        assert 2-sum < 0.0000001 #floating points
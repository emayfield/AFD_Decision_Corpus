import pytest
from tests.fixtures import basic_server
from endpoints.data.user import User

def test_get_all_users(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    assert len(all) >= 4

def test_get_one_user(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    for key in all:
        code, one = basic_server.users.get_by_id(key)
        assert code == 200
        assert type(one) is User
    code, broken_link = basic_server.users.get_by_id(-1)
    assert code == 404
    assert broken_link is None

def test_users_have_names(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    for key in all:
        # Test direct access
        code, one = basic_server.users.get_by_id(key)
        assert code == 200
        assert type(one.name) is str
        assert len(one.name) > 0
        # Test function access.
        code, name = basic_server.users.get_name(key)
        assert type(name) is str
        assert len(name) > 0
    
def test_get_id_by_name(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    for key in all:
        name = basic_server.users.get_name(key)
        code, retrieve = basic_server.users.get_id_by_name(name)
        assert code == 200
        assert type(retrieve) == int
        assert retrieve == key
    false_name = "nobody in particular"
    code, false_id = basic_server.users.get_id_by_name(false_name)
    assert code == 404
    assert false_id is None

def test_put_contribution_id(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    for key in all:
        code, user = basic_server.users.get_by_id(key)
        assert code == 200
        num_base_contribs = len(user.contributions)
        code, user_id = basic_server.users.put_contribution_id(key, 400000000, 1451606400)
        num_new_contribs = len(user.contributions)
        assert num_new_contribs == num_base_contribs + 1

def test_get_users_by_tenure(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    prev_cohort_min_size = 99999
    prev_cohort_max_size = 0
    at_least_one_min_change = False
    at_least_one_max_change = False
    for i in range(0,5):
        code, cohort = basic_server.users.get_users_by_tenure(min=i)
        assert len(cohort) <= len(all)
        assert len(cohort) <= prev_cohort_min_size
        if len(cohort) != prev_cohort_min_size:
            at_least_one_min_change = True
        prev_cohort_min_size = len(cohort)
        code, cohort = basic_server.users.get_users_by_tenure(max=i)
        assert len(cohort) >= prev_cohort_max_size
        if len(cohort) != prev_cohort_max_size:
            at_least_one_max_change = True
        prev_cohort_max_size = len(cohort)
    assert at_least_one_min_change
    assert at_least_one_max_change

def test_get_nth_contribution(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    for key in all:
        code, user = basic_server.users.get_by_id(key)
        most_recent_timestamp = 0
        for i in range(0,5):
            code, user_n = basic_server.users.get_nth_contribution(key, i)
            if code == 200:
                time = -1
                assert type(user_n) is int
                if str(user_n)[0] == '4':
                    code, time = basic_server.votes.get_timestamp(user_n)
                if str(user_n)[0] == '5':
                    code, time = basic_server.comments.get_timestamp(user_n)
                if str(user_n)[0] == '6':
                    code, time = basic_server.nominations.get_timestamp(user_n)
                assert user_n > 0 and time >= most_recent_timestamp
                most_recent_timestamp = time
            elif code == 202:
                assert i == len(user.contributions)
            elif code == 404:
                assert i > len(user.contributions)

def test_get_contributions(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    at_least_one_user_contributes = False
    for key in all:
        code, contribs = basic_server.users.get_contributions(key)
        assert code == 200
        assert type(contribs) is list
        if len(contribs) > 0:
            at_least_one_user_contributes = True
        for contrib_id in contribs:
            assert type(contrib_id) == int
            contrib_code = str(contrib_id)[0]
            assert contrib_code in ["4","5","6"]
    assert at_least_one_user_contributes

def test_get_participation_breakdown(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    for key in all:        
        code, breakdown = basic_server.users.get_participation_breakdown(key)
        at_least_one_contrib_each = False
        for k in ["Nominations","Votes","Comments","Outcomes"]:
            assert k in breakdown.keys()
            assert type(breakdown[k]) is int
            if breakdown[k] > 0:
                at_least_one_contrib_each = True
        assert at_least_one_contrib_each

def test_get_tenure_at_contribution(basic_server):
    code, all = basic_server.users.get_all()
    assert code == 200
    at_least_one_user_has_many_contribs = False
    for key in all:
        code, user = basic_server.users.get_by_id(key)
        assert code == 200
        contrib_tuples = []
        for i, contrib_tuple in enumerate(user.contributions):
            contrib_tuples.append(contrib_tuple)
        contrib_tuples = sorted(contrib_tuples, key=lambda x: x[1])
        for i, contrib_tuple in enumerate(contrib_tuples):
            contrib_id, timestamp = contrib_tuple

            code, tenure = basic_server.users.get_tenure_at_contribution(key, contrib_id)
            assert contrib_id > 0 and code == 200
            assert tenure == i
            if i > 3:
                at_least_one_user_has_many_contribs = True
    assert at_least_one_user_has_many_contribs
        
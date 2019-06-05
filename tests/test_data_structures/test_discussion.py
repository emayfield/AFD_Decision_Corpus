from tests.fixtures import basic_server
from endpoints.data.discussion import Discussion

def test_get_all_discussions(basic_server):
    code, all = basic_server.discussions.get_all()    
    assert code == 200
    assert len(all) >= 3

def test_get_one_discussion(basic_server):
    code, all = basic_server.discussions.get_all()
    assert code == 200
    for key in all:
        code, one = basic_server.discussions.get_by_id(key)
        assert code == 200
        assert type(one) is Discussion
    code, broken_link = basic_server.discussions.get_by_id(-1)
    assert code == 404
    assert broken_link is None

def test_discussions_have_titles(basic_server):
    code, all = basic_server.discussions.get_all()
    assert code == 200
    for key in all:
        code, one = basic_server.discussions.get_by_id(key)
        assert code == 200
        # Test direct access
        assert type(one.title) is str
        assert len(one.title) > 0  
        # Test function access
        code, title = basic_server.discussions.get_title(key)
        assert code == 200
        assert type(title) is str
        assert len(title) > 0

def test_get_id_by_title(basic_server):
    code, all = basic_server.discussions.get_all()
    assert code == 200
    for key in all:
        code, title = basic_server.discussions.get_title(key)
        assert code == 200
        code, retrieve_id = basic_server.discussions.get_id_by_title(title)
        assert code == 200
        assert type(retrieve_id) is int
        assert key == retrieve_id
    false_title = "there is no article with this title"
    code, retrieved_title = basic_server.discussions.get_id_by_title(false_title)
    assert code == 404
    assert retrieved_title is None

def test_discussions_have_timestamps(basic_server):
    code, all = basic_server.discussions.get_all()
    assert code == 200
    for key in all:
        code, vote_ids = basic_server.votes.get_votes_by_discussion(key)
        assert code == 200
        code, disc_timestamps = basic_server.discussions.get_timestamps(key)
        assert code == 200
        assert len(disc_timestamps) >= len(vote_ids)

def test_put_contribution(basic_server):
    code, all = basic_server.discussions.get_all()
    assert code == 200
    for key in all:
        code, disc_timestamps = basic_server.discussions.get_timestamps(key)
        num_timestamps = len(disc_timestamps)
        assert key > 0 and num_timestamps > 0
        assert code == 200
        basic_server.discussions.put_contribution(key, 400000000, 1485907200)
        code, updated_disc_timestamps = basic_server.discussions.get_timestamps(key)
        assert key > 0 and len(updated_disc_timestamps) == num_timestamps + 1

def test_get_timestamp_range(basic_server):
    code, all = basic_server.discussions.get_all()
    assert code == 200
    for key in all:
        code, disc_timestamps = basic_server.discussions.get_timestamps(key)
        code, timestamp_range = basic_server.discussions.get_timestamp_range(key)
        assert type(timestamp_range) is tuple
        assert len(timestamp_range) == 2
        assert timestamp_range[0] in disc_timestamps
        assert timestamp_range[1] in disc_timestamps
        if len(disc_timestamps) > 1:
            assert timestamp_range[0] < timestamp_range[1]

def test_get_discussions_by_timestamps(basic_server):
    code, all = basic_server.discussions.get_all()
    assert code == 200
    code, all_timestamped = basic_server.discussions.get_discussions_by_timestamps()
    assert len(all) == len(all_timestamped)
    for key in all:
        code, disc_timestamps = basic_server.discussions.get_timestamp_range(key)
        early = disc_timestamps[0]
        late = disc_timestamps[1]
        code, dont_exclude_early = basic_server.discussions.get_discussions_by_timestamps(start=early+1)
        code, exclude_late = basic_server.discussions.get_discussions_by_timestamps(start=late+1)
        assert len(exclude_late) < len(dont_exclude_early)
        code, exclude_strict = basic_server.discussions.get_discussions_by_timestamps(start=early+1, strict=True)
        assert len(exclude_strict) < len(dont_exclude_early)

def test_get_outcome(basic_server):
    code, all = basic_server.discussions.get_all()
    assert code == 200
    code, all_outcomes = basic_server.outcomes.get_all()
    assert code == 200
    at_least_one_outcome_exists = False
    for key in all:
        code, outcome_id = basic_server.discussions.get_outcome_id(key)
        assert (code == 200 or code == 404)
        if code == 200:
            at_least_one_outcome_exists = True
            assert type(outcome_id) is int
            assert outcome_id in all_outcomes
        if code == 404:
            assert outcome_id is None
    assert at_least_one_outcome_exists


def test_get_contributions(basic_server):
    code, all = basic_server.discussions.get_all()
    assert code == 200
    something_happens_in_at_least_one_discussion = False
    for key in all:
        code, contribs = basic_server.discussions.get_contributions(key)
        assert code == 200
        assert type(contribs) is list
        if len(contribs) > 0:
            something_happens_in_at_least_one_discussion = True
        for contrib_id in contribs:
            assert type(contrib_id) == int
            contrib_code = str(contrib_id)[0]
            assert contrib_code in ["3", "4","5","6"]
    assert something_happens_in_at_least_one_discussion

def test_get_contributions_at_time(basic_server):
    code, all = basic_server.discussions.get_all()
    assert code == 200
    for key in all:
        at_least_one_vote_per_discussion_exists = False
        code, contrib_ids = basic_server.discussions.get_contributions(key)
        count_all = len(contrib_ids)
        assert count_all > 0
        for c in contrib_ids:
            contrib_code = str(c)[0]
            if contrib_code == "4":
                at_least_one_vote_per_discussion_exists = True
                code, vote_timestamp = basic_server.votes.get_timestamp(c)
                assert type(vote_timestamp) is int
                code, contribs_after = basic_server.discussions.get_contributions_at_time(key, vote_timestamp+1)
                code, contribs_prior = basic_server.discussions.get_contributions_at_time(key, vote_timestamp-1)
                assert len(contribs_after) == len(contribs_prior) + 1
                assert len(contribs_prior) < count_all
        assert at_least_one_vote_per_discussion_exists
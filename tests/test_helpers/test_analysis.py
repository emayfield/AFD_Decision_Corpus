from tests.fixtures import basic_server
from endpoints.data.discussion import Discussion

# This method is likely going away, so we're not testing it for now.
def test_get_success_status(basic_server):
    code, disc_ids = basic_server.discussions.get_all()
    assert code == 200
    for disc_id in disc_ids:
        code, disc_obj = basic_server.discussions.get_by_id(disc_id)
        assert code == 200
        assert type(disc_obj) is Discussion
        code, outcome_id = basic_server.discussions.get_outcome_id(disc_id)
        assert code == 200
        code, outcome_label = basic_server.outcomes.get_label(outcome_id, normalized=2)
        assert code == 200
        assert type(outcome_label) is str
        assert outcome_label in ["Keep", "Delete", "Merge", "Redirect", "Other"]
        contribs = disc_obj.contributions
        for (contrib_id, timestamp) in contribs:
            val = basic_server.analysis.get_success_status(contrib_id)
            assert contrib_id > 0 and val is not None
            code, success_eval = val
            is_vote = basic_server.util.is_vote(contrib_id)
            is_outcome = basic_server.util.is_outcome(contrib_id)
            is_comment = basic_server.util.is_comment(contrib_id)
            is_nomination = basic_server.util.is_nomination(contrib_id)
            if is_outcome:
                assert contrib_id > 0 and success_eval == "Outcome"
            if is_vote:
                code, vote_label = basic_server.votes.get_label(contrib_id, normalized=2)
                assert code == 200
                assert type(vote_label) == str
                assert vote_label in ["Keep", "Delete", "Merge", "Redirect", "Other"]
                if vote_label == "Other" or outcome_label == "Other":
                    assert success_eval == "Vote Unclear"
                else:
                    if vote_label == outcome_label:
                        assert success_eval == "Vote Win"
                    else:
                        assert success_eval == "Vote Lose"
            if is_comment:
                assert success_eval == "Nonvoting"
            if is_nomination:
                if outcome_label == "Delete":
                    assert success_eval == "Nom Win"
                elif outcome_label == "Keep":
                    assert success_eval == "Nom Lose"
                elif outcome_label == "Other":
                    assert success_eval == "Nom Unclear"

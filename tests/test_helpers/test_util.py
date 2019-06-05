from tests.fixtures import basic_server

def test_year_ranges_work(basic_server):
    for year in range(2005, 2019):
        code, endpoints = basic_server.util.get_timestamps_for_year(year)
        assert code == 200
        assert type(endpoints) is tuple
        (start, end) = endpoints
        assert type(start) is float and type(end) is float
        assert end-start == 31536000 or end-start == 31622400 # leap year

def test_boolean_evaluators_work(basic_server):
    code, votes = basic_server.votes.get_all()
    for vote in votes:
        print(vote)
        is_vote = basic_server.util.is_vote(vote)
        is_comment = basic_server.util.is_comment(vote)
        is_nomination = basic_server.util.is_nomination(vote)
        assert is_vote
        assert not is_comment
        assert not is_nomination

    code, comments = basic_server.comments.get_all()
    for comment in comments:
        is_vote = basic_server.util.is_vote(comment)
        is_comment = basic_server.util.is_comment(comment)
        is_nomination = basic_server.util.is_nomination(comment)
        assert not is_vote
        assert is_comment
        assert not is_nomination
        
    code, nominations = basic_server.nominations.get_all()
    for nomination in nominations:
        is_vote = basic_server.util.is_vote(nomination)
        is_comment = basic_server.util.is_comment(nomination)
        is_nomination = basic_server.util.is_nomination(nomination)
        assert not is_vote
        assert not is_comment
        assert is_nomination
        
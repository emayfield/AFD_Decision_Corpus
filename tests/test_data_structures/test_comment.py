from endpoints.data.comment import Comment
from tests.fixtures import basic_server

def test_get_all_comments(basic_server):
    code, all = basic_server.comments.get_all()
    assert code == 200
    assert len(all) >= 2

def test_get_one_comment(basic_server):
    code, all = basic_server.comments.get_all()
    assert code == 200
    for key in all:
        code, one = basic_server.comments.get_by_id(key)
        assert code == 200
        assert type(one) is Comment
    code, broken_link = basic_server.comments.get_by_id(-1)
    assert code == 404
    assert broken_link is None

def test_comments_have_texts(basic_server):
    code, all = basic_server.comments.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, text = basic_server.comments.get_text(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(text) is str
        elif code == 404:
            assert text is None

def test_comments_have_timestamps(basic_server):
    code, all = basic_server.comments.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, timestamp = basic_server.comments.get_timestamp(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(timestamp) is int
        elif code == 404:
            assert timestamp is None

def test_comments_have_users(basic_server):
    code, all = basic_server.comments.get_all()
    assert code == 200
    for key in all:
        code, one = basic_server.comments.get_user_id(key)
        assert code == 200
        assert type(one) is int
        code, user = basic_server.users.get_by_id(one)
        assert code == 200
    
    
def test_comments_have_discussion_ids(basic_server):
    code, all = basic_server.comments.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, disc_id = basic_server.comments.get_discussion_id(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(disc_id) is int
            disc_id_str = str(disc_id)
            assert disc_id_str[0] == "1"
        elif code == 404:
            assert disc_id is None


def test_get_comments_by_timestamps(basic_server):
    code, comment_ids = basic_server.comments.get_all()
    assert code == 200
    code, all_comment_ids = basic_server.comments.get_comments_by_timestamps()
    assert code == 200
    assert len(all_comment_ids) == len(comment_ids)

    active_timestamps = sorted([basic_server.comments.get_by_id(v)[1].timestamp for v in comment_ids])
    earliest = active_timestamps[0]
    latest = active_timestamps[-1]
    code, filtered_comment_ids = basic_server.comments.get_comments_by_timestamps(end=latest-1)
    assert len(filtered_comment_ids) == len(comment_ids) - 1
    code, filtered_comment_ids = basic_server.comments.get_comments_by_timestamps(start=earliest+1)
    assert len(filtered_comment_ids) == len(comment_ids) - 1
    code, filtered_comment_ids = basic_server.comments.get_comments_by_timestamps(start=earliest+1, end = latest-1)
    assert len(filtered_comment_ids) == len(comment_ids) - 2
    code, filtered_comment_ids = basic_server.comments.get_comments_by_timestamps(start=latest+1)
    assert len(filtered_comment_ids) == 0
    

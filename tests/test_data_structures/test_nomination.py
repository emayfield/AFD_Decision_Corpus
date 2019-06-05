from endpoints.data.nomination import Nomination
from tests.fixtures import basic_server

def test_get_all_nominations(basic_server):
    code, all = basic_server.nominations.get_all()
    assert code == 200
    assert len(all) >= 2

def test_get_one_nomination(basic_server):
    code, all = basic_server.nominations.get_all()
    assert code == 200
    for key in all:
        code, one = basic_server.nominations.get_by_id(key)
        assert code == 200
        assert type(one) is Nomination
    code, broken_link = basic_server.nominations.get_by_id(-1)
    assert code == 404
    assert broken_link is None

def test_nominations_have_texts(basic_server):
    code, all = basic_server.nominations.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, text = basic_server.nominations.get_text(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(text) is str
        elif code == 404:
            assert text is None

def test_nominations_have_timestamps(basic_server):
    code, all = basic_server.nominations.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, timestamp = basic_server.nominations.get_timestamp(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(timestamp) is int
        elif code == 404:
            assert timestamp is None

def test_nominations_have_users(basic_server):
    code, all = basic_server.nominations.get_all()
    assert code == 200
    for key in all:
        code, one = basic_server.nominations.get_user_id(key)
        assert code == 200
        assert type(one) is int
        code, user = basic_server.users.get_by_id(one)
        assert code == 200
    
    
def test_nominations_have_discussion_ids(basic_server):
    code, all = basic_server.nominations.get_all()
    assert code == 200
    for key in all:
        # Test function access.
        code, disc_id = basic_server.nominations.get_discussion_id(key)
        assert (code == 200 or code == 404)
        if code == 200:
            assert type(disc_id) is int
            disc_id_str = str(disc_id)
            assert disc_id_str[0] == "1"
        elif code == 404:
            assert disc_id is None
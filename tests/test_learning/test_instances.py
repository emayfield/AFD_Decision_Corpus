from tests.fixtures import instance_server

from endpoints.learning.instance import Instance

def test_get_all_instance(instance_server):
    code, all = instance_server.instances.get_all()
    assert code == 200
    assert len(all) >= 2

def test_get_one_instance(instance_server):
    code, all = instance_server.instances.get_all()
    assert code == 200
    for key in all:
        code, one = instance_server.instances.get_by_id(key)
        assert code == 200
        assert type(one) is Instance
    code, broken_link = instance_server.instances.get_by_id(-1)
    assert code == 404
    assert broken_link is None

def test_get_contribution_ids(instance_server):
    code, all = instance_server.instances.get_all()
    assert code == 200
    assert len(all) > 0
    for key in all:
        code, contrib_ids = instance_server.instances.get_contribution_ids(key)
        assert code == 200
        assert len(contrib_ids) > 0
        at_least_one_vote_found = False
        for contrib_id in contrib_ids:
            assert type(contrib_id) == int
            contrib_code = str(contrib_id)[0]
            if contrib_code == "4":
                code, vote = instance_server.votes.get_by_id(contrib_id)
                assert code == 200
                at_least_one_vote_found = True
        assert at_least_one_vote_found

def test_get_y(instance_server):
    code, all = instance_server.instances.get_all()
    assert code == 200
    for key in all:
        code, disc_id = instance_server.instances.get_discussion_id(key)
        code, outcome_id = instance_server.discussions.get_outcome_id(disc_id)
        code, label = instance_server.outcomes.get_label(outcome_id, normalized = 2)
        code, y = instance_server.instances.get_y(key)
        assert code == 200
        assert type(y) is str
        assert y == label


def test_get_discussion_id(instance_server):
    code, all = instance_server.instances.get_all()
    assert code == 200
    assert len(all) > 0
    for key in all:
        code, discussion_id = instance_server.instances.get_discussion_id(key)
        assert code == 200
        assert type(discussion_id) is int
        code, discussion = instance_server.discussions.get_by_id(discussion_id)
        assert code == 200
        assert discussion is not None
    
def test_put_vector_id(instance_server):
    code, all = instance_server.instances.get_all()
    for key in all:
        code, vector_ids = instance_server.instances.get_vector_ids(key)
        original_length = len(vector_ids)
        assert code == 200
        assert original_length > 0
        insert_id = -200000000
        code, new_vector_id = instance_server.instances.put_vector_id(key, insert_id)
        assert code == 200
        assert new_vector_id == insert_id
        code, new_vector_ids = instance_server.instances.get_vector_ids(key)
        updated_length = len(new_vector_ids)
        assert code == 200
        assert updated_length > 0
        assert updated_length == original_length + 1
        
def test_get_vector_ids(instance_server):
    code, all = instance_server.instances.get_all()
    for key in all:
        code, vector_ids = instance_server.instances.get_vector_ids(key)
        assert code == 200
        for v in vector_ids:
            code, vector = instance_server.vectors.get_by_id(v)
            assert code == 200
            x = vector.x
            assert len(x) > 0

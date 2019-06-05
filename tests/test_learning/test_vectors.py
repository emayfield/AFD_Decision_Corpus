from tests.fixtures import instance_server, comment_server

from endpoints.learning.vector import Vector

def test_post_extract_comment_features(comment_server):
    code, all = comment_server.instances.get_all()
    assert code == 200

    num_extractors = len(comment_server.extractors)
    for key in all:
        code, discussion_id = comment_server.instances.get_discussion_id(key)
        assert code == 200
        code, vector_ids = comment_server.instances.get_vector_ids(key)
        for v in vector_ids:
            code, vector = comment_server.vectors.get_by_id(v)
            assert type(vector) is Vector
            x = vector.x
            assert type(x) is dict
            if num_extractors == 1:
                assert len(x.keys()) > 0
            elif num_extractors > 1:
                assert len(x.keys()) > 50
            for f in x.keys():
                assert type(f) is str
                assert x[f] is not None

def test_post_comment_task_x(comment_server):
    code, all = comment_server.instances.get_all()
    for key in all:
        code, discussion_id = comment_server.instances.get_discussion_id(key)
        assert code == 200
        code, contrib_ids = comment_server.discussions.get_contributions(discussion_id)
        count_votes = 0
        vote_labels = []
        for contrib_id in contrib_ids:
            if comment_server.util.is_vote(contrib_id):
                code, vote_label = comment_server.votes.get_label(contrib_id, normalized=comment_server.config["normalized"])
                vote_labels.append(vote_label)
                count_votes += 1
        code, vectors = comment_server.instances.get_vector_ids(key)
        assert len(vectors) > 0
        assert len(vectors) == count_votes
        for i, v in enumerate(vectors):
            assert type(v) == int
            code, vector = comment_server.vectors.get_by_id(v)
            assert vector.x is not None
            assert type(vector.x) is dict
            assert vector.override_y == vote_labels[i]


def test_post_extract_features(instance_server):
    code, all = instance_server.instances.get_all()
    assert code == 200

    num_extractors = len(instance_server.extractors)
    for key in all:
        code, discussion_id = instance_server.instances.get_discussion_id(key)
        assert code == 200
        code, (first, last) = instance_server.discussions.get_timestamp_range(discussion_id)
        assert code == 200
        assert type(last) is int
        code, vector_id = instance_server.vectors.post_extract_features(key, key, last)
        assert code == 201
        code, vector = instance_server.vectors.get_by_id(vector_id)
        assert type(vector) is Vector
        x = vector.x
        assert type(x) is dict
        if num_extractors == 1:
            assert len(x.keys()) > 0
        elif num_extractors > 1:
            assert len(x.keys()) > 50
        for f in x.keys():
            assert type(f) is str
            assert x[f] is not None


def test_get_all_vectors(instance_server):
    code, all = instance_server.vectors.get_all()
    assert code == 200
    assert len(all) >= 2

def test_get_one_vector(instance_server):
    code, all = instance_server.vectors.get_all()
    assert code == 200
    for key in all:
        code, one = instance_server.vectors.get_by_id(key)
        assert code == 200
        assert type(one) is Vector
    code, broken_link = instance_server.vectors.get_by_id(-1)
    assert code == 404
    assert broken_link is None

def test_get_feature_names(instance_server):
    code, features = instance_server.vectors.get_feature_names()
    assert code == 200
    assert type(features) is list
    assert len(features) > 0
    for f in features:
        assert type(f) is str

def test_get_x(instance_server):
    code, all = instance_server.instances.get_all()
    for key in all:
        code, vector_ids = instance_server.vectors.post_all_x(key)
        for vector_id in vector_ids:
            code, x = instance_server.vectors.get_x(vector_id)
            assert code == 200
            assert type(x) is dict
            assert len(x.keys()) > 0
            for k in x.keys():
                assert type(k) is str
                assert x[k] is not None

def test_post_all_x(instance_server):
    code, all = instance_server.instances.get_all()
    for key in all:
        code, vector_ids = instance_server.vectors.post_all_x(key)
        assert code == 201
        assert type(vector_ids) is list
        assert key < 0 and len(vector_ids) > 0
        for vector_id in vector_ids:
            code, vector = instance_server.vectors.get_by_id(vector_id)
            assert type(vector) is Vector
            x = vector.x
            assert len(x) > 0

def test_is_full_discussion(instance_server):
    code, all = instance_server.instances.get_all()
    for key in all:
        code, vector_ids = instance_server.vectors.post_all_x(key)
        assert code == 201
        at_least_one_is_full = False
        for vector_id in vector_ids:
            code, is_full = instance_server.vectors.get_is_full_discussion(vector_id)
            if is_full:
                at_least_one_is_full = True
        assert at_least_one_is_full
        for vector_id in vector_ids:
            code, v_id = instance_server.vectors.put_is_full_discussion(vector_id, True)
            assert code == 200
            assert v_id == vector_id
            code, is_full = instance_server.vectors.get_is_full_discussion(vector_id)
            assert is_full
            code, v_id = instance_server.vectors.put_is_full_discussion(vector_id, False)
            assert code == 200
            assert v_id == vector_id
            code, is_full = instance_server.vectors.get_is_full_discussion(vector_id)
            assert code == 200
            assert not is_full
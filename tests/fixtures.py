import pytest
from server import DebateServer

@pytest.fixture
def basic_user():
    return {
        "username":"elijah",
        "id":1
    }

@pytest.fixture
def basic_server():
    config = {
        "extractors": ["TALLY"],
        "normalized": 2,
        "strict_discussions": False
    }
    server = DebateServer(config)
    server.import_corpus("test_corpus.json")
    return server

@pytest.fixture
def bert_server():
    config = {
        "extractors": ["BERT"],
        "normalized": 2,
        "strict_discussions": False
    }
    server = DebateServer(config)
    server.import_corpus("test_corpus.json")
    code, disc_ids = server.discussions.get_all()
    vector_ids = []
    for disc_id in disc_ids:
        code, instance_id = server.instances.post_instance(disc_id, 999999999999)
        if code == 201:
            code, v_ids = server.vectors.post_all_x(instance_id)
            vector_ids = vector_ids + v_ids
    code, feature_names = server.vectors.get_feature_names()
    code, corpus = server.corpora.post_corpus(vector_ids)
    return server

@pytest.fixture
def instance_server():
    config = {
        "extractors": ["TALLY"],
        "normalized": 2,
        "strict_discussions": False
    }
    server = DebateServer(config)
    server.import_corpus("test_corpus.json")
    code, disc_ids = server.discussions.get_all()
    vector_ids = []
    for disc_id in disc_ids:
        code, instance_id = server.instances.post_instance(disc_id, 999999999999)
        if code == 201:
            code, v_ids = server.vectors.post_all_x(instance_id)
            vector_ids = vector_ids + v_ids
    code, feature_names = server.vectors.get_feature_names()
    code, corpus = server.corpora.post_corpus(vector_ids)
    return server

@pytest.fixture
def comment_server():
    config = {
        "extractors": ["TALLY"],
        "normalized": 2,
        "strict_discussions": False
    }
    server = DebateServer(config)
    server.import_corpus("test_corpus.json")
    code, disc_ids = server.discussions.get_all()
    vector_ids = []
    for disc_id in disc_ids:
        code, instance_id = server.instances.post_instance(disc_id, 999999999999)
        if code == 201:
            code, v_ids = server.vectors.post_comment_task_x(instance_id)
            vector_ids = vector_ids + v_ids
    code, feature_names = server.vectors.get_feature_names()
    code, corpus = server.corpora.post_corpus(vector_ids)
    return server


@pytest.fixture
def learning_server():
    config = {
        "extractors": ["TALLY"],
        "normalized": 2,
        "strict_discussions": False
    }
    server = DebateServer(config)
    server.import_corpus("test_corpus.json")
    code, disc_ids = server.discussions.get_all()
    vector_ids = []
    for disc_id in disc_ids:
        code, instance_id = server.instances.post_instance(disc_id, 999999999999)
        if code == 201:
            code, v_ids = server.vectors.post_all_x(instance_id, multiply=True)
            vector_ids = vector_ids + v_ids
    code, corpus_id = server.corpora.post_corpus(vector_ids)
    print(code)
    code, predictions_id = server.prediction.post_prediction(corpus_id)
    print(code)
    return server


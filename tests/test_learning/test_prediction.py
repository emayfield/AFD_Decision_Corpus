from tests.fixtures import learning_server, instance_server
from endpoints.learning.prediction import Prediction
import numpy as np

def test_get_all_predictions(learning_server):
    pass
    code, all = learning_server.prediction.get_all()
    assert code == 200
    assert len(all) > 0

def test_get_one_prediction(learning_server):
    code, all = learning_server.prediction.get_all()
    assert code == 200
    for key in all:
        code, one = learning_server.prediction.get_by_id(key)
        assert code == 200
        assert type(one) is Prediction
        assert type(one.preds_y) is list
        assert len(one.preds_y) > 2
        assert type(one.probs_y) is list
        for p in one.probs_y:
            p_sum = 0
            assert type(p) is np.ndarray
            assert len(p) > 0
            for l in p:
                p_sum += l
            assert 1-p_sum < 0.000001
        assert one.accuracy > 0

        for i in range(len(one.preds_y)):
            code, pred = learning_server.prediction.get_prediction(key, i)
            assert code == 200
            assert pred == one.preds_y[i]
            code, probs = learning_server.prediction.get_probabilities(key, i)
            assert code == 200
            assert type(probs) is np.ndarray
            for j in range(len(probs)):
                assert probs[j] == one.probs_y[i][j]
    code, broken_link = learning_server.prediction.get_by_id(-1)
    assert code == 404
    assert broken_link is None

def test_put_influences(learning_server):
    code, all = learning_server.prediction.get_all()
    assert code == 200
    for key in all:
        code, modified_vote_ids = learning_server.prediction.put_influences(key)
        assert code == 200
        assert len(modified_vote_ids) > 0
        at_least_one_vote = False
        for target_id in modified_vote_ids:
            contrib_code = str(target_id)[0]
            if contrib_code == "4":
                code, vote_influence = learning_server.votes.get_influence(target_id)
                assert code == 200
                assert type(vote_influence) is np.float64
                assert vote_influence != 0
                at_least_one_vote = True
        assert at_least_one_vote

def test_get_corpus_id(learning_server):
    code, all = learning_server.prediction.get_all()
    assert code == 200
    for key in all:
        code, corpus_id = learning_server.prediction.get_corpus_id(key)
        assert code == 200
        assert type(corpus_id) is int
        code, corpus = learning_server.corpora.get_by_id(corpus_id)
        assert code == 200
        assert corpus is not None
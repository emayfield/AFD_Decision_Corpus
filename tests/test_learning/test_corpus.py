from tests.fixtures import instance_server
import numpy as np

from endpoints.learning.corpus import Corpus

def test_get_all_corpora(instance_server):
    code, all = instance_server.corpora.get_all()
    assert code == 200
    assert len(all) > 0

def test_get_one_corpus(instance_server):
    code, all = instance_server.corpora.get_all()
    assert code == 200
    for key in all:
        code, one = instance_server.corpora.get_by_id(key)
        assert code == 200
        assert type(one) is Corpus
    code, broken_link = instance_server.corpora.get_by_id(-1)
    assert code == 404
    assert broken_link is None

def test_get_vector_ids(instance_server):
    code, all = instance_server.corpora.get_all()
    assert code == 200
    for key in all:
        code, corpus = instance_server.corpora.get_by_id(key)
        code, vector_ids = instance_server.corpora.get_vector_ids(key)
        assert len(vector_ids) == len(corpus.vector_ids)
        assert len(vector_ids) > 0
        for v in vector_ids:
            code, vector = instance_server.vectors.get_by_id(v)
            assert code == 200
            assert vector is not None

def test_get_feature_names(instance_server):
    code, all = instance_server.corpora.get_all()
    assert code == 200
    for key in all:
        all_names = {}
        code, feature_names = instance_server.corpora.get_feature_names(key)
        assert type(feature_names) is list
        assert len(feature_names) > 0
        for f in feature_names:
            assert type(f) is str
            assert len(f) > 0
            assert f not in all_names.keys()
            all_names[f] = 1
        
def test_get_y(instance_server):
    code, all = instance_server.corpora.get_all()
    assert code == 200
    for key in all:
        code, corpus = instance_server.corpora.get_by_id(key)
        num_instances = len(corpus.vector_ids)
        code, y = instance_server.corpora.get_y(key)
        assert code == 200
        assert type(y) is list
        assert len(y) > 0
        assert len(y) == num_instances
        for val in y:
            assert type(val) is str
    
def test_x_numpy(instance_server):
    code, all = instance_server.corpora.get_all()
    assert code == 200
    for key in all:
        code, feature_names, x_np = instance_server.corpora.get_x_numpy(key)
        assert type(feature_names) is dict
        assert type(x_np) == np.ndarray
        for f in feature_names.keys():
            assert type(f) is str
            assert len(f) > 0
            assert type(feature_names[f]) is not None
        print(x_np.shape)
        x,y = x_np.shape
        assert x > 0
        assert y > 0
        at_least_one_feature_nonzero = False
        for i in range(x):
            for j in range(y):
                if x_np[i,j] > 0:
                    at_least_one_feature_nonzero = True
        assert at_least_one_feature_nonzero
        
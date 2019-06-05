from tests.fixtures import instance_server, bert_server

def test_extractors_have_same_size(instance_server, bert_server):
    code, tally_instances = instance_server.instances.get_all()
    assert code == 200
    code, bert_instances = bert_server.instances.get_all()
    assert code == 200
    assert len(tally_instances) > 0
    assert len(bert_instances) > 0
    assert len(tally_instances) == len(bert_instances)

    tally_keys = list(tally_instances)
    bert_keys = list(bert_instances)
    for i in range(len(tally_keys)):
        code, tally_vectors = instance_server.instances.get_vector_ids(tally_keys[i])
        code, bert_vectors = bert_server.instances.get_vector_ids(bert_keys[i])
        assert len(tally_vectors) > 0
        assert len(bert_vectors) > 0
        assert len(tally_vectors) == len(bert_vectors)



def test_get_feature_names(instance_server):
    extractors = instance_server.extractors
    all_names_across_extractors = {}
    for extractor in extractors:
        code, names = extractor.feature_names()
        assert code == 200
        assert type(names) is list
        assert len(names) > 0
        for name in names:
            assert type(name) is str
            assert len(name) > 0
            assert name not in all_names_across_extractors.keys()
            all_names_across_extractors[name] = 1

def test_extract_features(instance_server):
    extractors = instance_server.extractors
    code, all = instance_server.instances.get_all()
    assert code == 200
    for key in all:
        code, discussion_id = instance_server.instances.get_discussion_id(key)
        code, (first, last) = instance_server.discussions.get_timestamp_range(discussion_id)
        assert code == 200
        assert type(last) is int
        for extractor in extractors:
            some_feature_is_not_zero = False
            features = extractor.feature_names()
            code, features = extractor.extract_features(key, last)
            assert code == 201
            assert type(features) is dict
            for feature_name in features.keys():
                assert type(feature_name) is str
                assert feature_name in features
                feature_value = features[feature_name]
                if feature_value != 0:
                    some_feature_is_not_zero = True
            assert some_feature_is_not_zero

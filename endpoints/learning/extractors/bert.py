from bert_serving.client import BertClient
import time
from endpoints.helpers.cache import lookup, store
import numpy as np
import json
import math

class BertEndpoint:

    bert = None

    f1 = 0
    f2 = 0
    f3 = 0
    cache_path = None

    function_key = ["bert"]

    def __init__(self, server):
        self.server = server
        self.dimensions = 768

        if BertEndpoint.bert is None:
            BertEndpoint.bert = BertClient()
            BertEndpoint.cache_path = open("cachepath","r").read().strip()
            
    
    def feature_names(self):
        return 200, ["D{}".format(i) for i in range(self.dimensions)]

    def single_contrib_features(self, contrib_id):
        code, val = lookup(BertEndpoint.cache_path, BertEndpoint.function_key, contrib_id)
        if code == 200:
            try:
                return json.loads(val)
            except:
                return None
        else:
            return None

    def extract_features(self, instance_id, vote_timestamp, contrib_ids=None):
        try:
            code, discussion_id = self.server.instances.get_discussion_id(instance_id)
            if contrib_ids is None:
                code, contrib_ids = self.server.discussions.get_contributions_at_time(discussion_id, vote_timestamp)

            vectors = []
            logs = []
            for contrib_id in contrib_ids:
                code, contrib_text = self.server.util.get_text(contrib_id)
                code, contrib_timestamp = self.server.util.get_timestamp(contrib_id)

                log_tokens = 0
                if contrib_text is not None and len(contrib_text.split()) > 0:
                    log_tokens = math.log(len(contrib_text.split()))
                code, val = lookup(BertEndpoint.cache_path, BertEndpoint.function_key, contrib_id)
                if code == 200:
                    encodes = None
                    try:
                        encodes = json.loads(val)
                    except: 
                        encodes = [0]*768
                    vectors.append(encodes)
                    logs.append(log_tokens)
                else:

                    if contrib_text is not None:
                        s1 = time.time()
                        to_bert = contrib_text.strip()
                        if len(to_bert) > 0:
                            encodes = BertEndpoint.bert.encode([to_bert])[0].tolist()
                            store(BertEndpoint.cache_path, BertEndpoint.function_key, contrib_id, json.dumps(encodes))
                            vectors.append(encodes)
                            logs.append(log_tokens)
                        else:
                            store(BertEndpoint.cache_path, BertEndpoint.function_key, contrib_id, "")
                        s2 = time.time()
                        BertEndpoint.f1 += (s2-s1)
                        if(instance_id%100==0):
                            print("{} {}".format(instance_id, BertEndpoint.f1))
            sum_embedding = np.zeros(self.dimensions)
            total_embeddings = 0
            if len(vectors) > 0:
                sum_token_logs = 0
                for i in range(len(vectors)):
                    this_embedding = [logs[i]*v for v in vectors[i]]
                    ma = max(this_embedding)
                    mi = min(this_embedding)
                    if not -1000 < mi <= ma < 1000:
                        print("-----")
                        print(ma)
                        print(mi)
                        print(i)
                    sum_token_logs += logs[i]

                    sum_embedding = np.add(sum_embedding, this_embedding)
                if sum_token_logs > 0:
                    sum_embedding = np.divide(sum_embedding, sum_token_logs)
            if(instance_id % 100 == 0):
                print("Embedded: instance {}, {} dimensions, {} texts".format(instance_id, len(sum_embedding), len(vectors)))
            x = list(np.array(sum_embedding))
            x_dict = {"D{}".format(i):x[i] for i in range(len(x))}
            return 201, x_dict
        except Exception as e:
            print(instance_id)
            print(e)
            return 500, None

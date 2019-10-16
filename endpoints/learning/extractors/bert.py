
import time
import torch
from endpoints.helpers.cache import lookup, store
import numpy as np
import json
import os
import math
from pytorch_transformers import BertTokenizer, BertModel, BertForMaskedLM

def import_bert_cache():
    cachepath = os.path.join("..","cache","bert_library")
    influence_cache = {}
    if (os.path.exists(cachepath)):
        categories = os.listdir(cachepath)
        for cat in categories:
            print(cat)
            if not os.path.isfile(cat):
                catpath = os.path.join(cachepath, cat)
                if os.path.exists(catpath):
                    subcat = os.listdir(catpath)
                    for sub in subcat:
                        subcatpath = os.path.join(catpath, sub)
                        if os.path.isfile(subcatpath) and "DS_Store" not in sub:
                            print(subcatpath)
                            cache_file = open(subcatpath, "r")
                            cache_line = cache_file.readline()
                            old_cache_line = None
                            line_type = 'content'
                            current_key = None
                            if len(cache_line) > 0:
                                current_key = int(cache_line)
                            while current_key is not None and cache_line != old_cache_line:
                                old_cache_line = cache_line
                                cache_line = cache_file.readline().strip()
                                if line_type == 'content':
                                    if len(cache_line) > 0:
                                        cache_json = json.loads(cache_line)
                                        influence_cache[current_key] = cache_json
                                        if current_key % 100 == 0:
                                            print("Keyed {}".format(current_key))
                                    line_type = 'blank'
                                elif line_type == 'key':
                                    if len(cache_line) > 0:
                                        current_key = int(cache_line)
                                    line_type = 'content'
                                elif line_type == 'blank':
                                    line_type = 'key'
    return influence_cache  


class BertEndpoint:

    bert = None

    f1 = 0
    f2 = 0
    f3 = 0
    cache_path = "../cache"

    function_key = ["bert_library"]

    def __init__(self, server):
        self.server = server
        self.dimensions = 768
        transformer_type = 'bert-base-uncased'
        self.tokenizer = BertTokenizer.from_pretrained(transformer_type)
        self.model = BertModel.from_pretrained(transformer_type)
        self.model.eval()

    def preprocess(self, text):
        modified_text = self.tokenizer.tokenize(text)
        if len(modified_text) > 510:
            modified_text = modified_text[0:510]
        modified_array = ['[CLS]'] + modified_text + ['[SEP]']
        indexed_tokens = self.tokenizer.convert_tokens_to_ids(modified_array)

        segments_ids = [0]*len(modified_array)

        # Convert inputs to PyTorch tensors
        tokens_tensor = torch.tensor([indexed_tokens])
        segments_tensors = torch.tensor([segments_ids])
        return tokens_tensor, segments_tensors

    def library_encode(self, text):
        tokens_tensor, segments_tensors = self.preprocess(text)
        with torch.no_grad():
            outputs = self.model(tokens_tensor, token_type_ids=segments_tensors)
            encoded_layers = outputs[0]

        # We have encoded our input sequence in a FloatTensor of shape (batch size, sequence length, model hidden dimension)
        return encoded_layers[0][0]
                
    
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
                            encodes = self.library_encode(to_bert).tolist()
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



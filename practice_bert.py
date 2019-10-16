import torch
from pytorch_transformers import BertTokenizer, BertModel, BertForMaskedLM

# OPTIONAL: if you want to have more information on what's happening under the hood, activate the logger as follows
import logging
logging.basicConfig(level=logging.INFO)

def preprocess(tokenizer, text):
    print("-----")
    modified_text = tokenizer.tokenize(text)
    print(modified_text)
    modified_array = ['[CLS]'] + modified_text + ['[SEP]']
    indexed_tokens = tokenizer.convert_tokens_to_ids(modified_array)
    print(modified_text)
    print(modified_array)
    print("----====")

    segments_ids = [0]*len(modified_array)

    # Convert inputs to PyTorch tensors
    tokens_tensor = torch.tensor([indexed_tokens])
    segments_tensors = torch.tensor([segments_ids])
    return tokens_tensor, segments_tensors




def sample_encode_input():
    # Load pre-trained model tokenizer (vocabulary)
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    # Load pre-trained model (weights)
    model = BertModel.from_pretrained('bert-base-uncased')
    # Set the model in evaluation mode to desactivate the DropOut modules
    # This is IMPORTANT to have reproductible results during evaluation!
    model.eval()

    test_sentences = ["Who was Jim Henson?", "Who framed Roger Rabbit?"]

    test_sentences_reversed = ["Who framed Roger Rabbit?", "Who was Jim Henson?"]

    for text in test_sentences:
        tokens_tensor, segments_tensors = preprocess(tokenizer, text)
        # Predict hidden states features for each layer
        with torch.no_grad():
            outputs = model(tokens_tensor, token_type_ids=segments_tensors)
            # In our case, the first element is the hidden state of the last layer of the Bert model
            encoded_layers = outputs[0]

        # We have encoded our input sequence in a FloatTensor of shape (batch size, sequence length, model hidden dimension)
        print(model.config.hidden_size)
        print(encoded_layers.shape)
        print(encoded_layers[0][0][0:5])


    for text in test_sentences_reversed:
        tokens_tensor, segments_tensors = preprocess(tokenizer, text)
        # Predict hidden states features for each layer
        with torch.no_grad():
            outputs = model(tokens_tensor, token_type_ids=segments_tensors)
            # In our case, the first element is the hidden state of the last layer of the Bert model
            encoded_layers = outputs[0]

        # We have encoded our input sequence in a FloatTensor of shape (batch size, sequence length, model hidden dimension)
        print(model.config.hidden_size)
        print(encoded_layers.shape)
        print(encoded_layers[0][0][0:5])

    

def sample_predict_token():
    # Load pre-trained model tokenizer (vocabulary)
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    # Tokenize input
    text = "[CLS] Who was Jim Henson ? [SEP] Jim Henson was a puppeteer [SEP]"
    tokenized_text = tokenizer.tokenize(text)

    # Mask a token that we will try to predict back with `BertForMaskedLM`
    masked_index = 8
    tokenized_text[masked_index] = '[MASK]'
    assert tokenized_text == ['[CLS]', 'who', 'was', 'jim', 'henson', '?', '[SEP]', 'jim', '[MASK]', 'was', 'a', 'puppet', '##eer', '[SEP]']

    # Convert token to vocabulary indices
    indexed_tokens = tokenizer.convert_tokens_to_ids(tokenized_text)
    # Define sentence A and B indices associated to 1st and 2nd sentences (see paper)
    segments_ids = [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]

    # Convert inputs to PyTorch tensors
    tokens_tensor = torch.tensor([indexed_tokens])
    segments_tensors = torch.tensor([segments_ids])
  
    model = BertForMaskedLM.from_pretrained('bert-base-uncased')
    model.eval()

    # If you have a GPU, put everything on cuda
    #tokens_tensor = tokens_tensor.to('cuda')
    #segments_tensors = segments_tensors.to('cuda')
    #model.to('cuda')

    # Predict all tokens
    with torch.no_grad():
        outputs = model(tokens_tensor, token_type_ids=segments_tensors)
        predictions = outputs[0]

    # confirm we were able to predict 'henson'
    predicted_index = torch.argmax(predictions[0, masked_index]).item()
    predicted_token = tokenizer.convert_ids_to_tokens([predicted_index])[0]
    print(predicted_token)
    assert predicted_token == 'henson'


if __name__ == "__main__":
    sample_encode_input()
#    sample_predict_token()






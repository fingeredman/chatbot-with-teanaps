from teanaps.handler import FileHandler

import configure as con

from gluonnlp.data import SentencepieceTokenizer
import numpy as np
from torch import nn
import torch
import pickle
       
class IntentClassifierBERT():  
    def __init__(self):
        with open(con.MODEL_CONFIG["bert"]["model_state_dict"], 'rb') as f:
            self.model_state_dict = pickle.load(f)
        with open(con.MODEL_CONFIG["bert"]["intent_id_to_name"], 'rb') as f:
            self.intent_id_to_name = pickle.load(f)
        with open(con.MODEL_CONFIG["bert"]["bertmodel"], 'rb') as f:
            self.bertmodel = pickle.load(f)
        with open(con.MODEL_CONFIG["bert"]["token_to_index"], 'rb') as f:
            self.token_to_index = pickle.load(f)
        with open(con.MODEL_CONFIG["bert"]["index_to_token"], 'rb') as f:
            self.index_to_token = pickle.load(f)
        self.tokenizer = SentencepieceTokenizer(con.MODEL_CONFIG["bert"]["tokenizer"])
        self.vocab = con.VOCAB
        self.fh = FileHandler()
        self.__load_intent_model()
        
    def parse(self, input_text, intent_count=1):
        input_text_lower = input_text.lower()
        list_of_input_ids = self.__sentence_to_token_index_list([input_text_lower])
        token_ids = torch.tensor([list_of_input_ids[0]+[1 for i in range(32-len(list_of_input_ids[0]))]])
        segment_ids = torch.tensor([[0 for i in range(len(token_ids[0]))]])
        valid_length = torch.tensor([len(list_of_input_ids[0])], dtype=torch.int32)
        result_list = self.model(token_ids, valid_length, segment_ids)
        result_list = [1/(1 + np.exp(-float(w))) for w in result_list[0]]
        intent_list = [(self.intent_id_to_name[i], w) for i, w in enumerate(result_list)]
        intent_list.sort(key=lambda elem: elem[1], reverse=True)
        return intent_list[:intent_count]
    
    def __load_intent_model(self):
        self.model = BERTClassifier(self.bertmodel, dr_rate=0.5, num_classes=len(self.intent_id_to_name))
        self.model.load_state_dict(self.model_state_dict)
                                    
    def __token_list_to_index_list(self, token_list):
        index_list = []
        for token in token_list:
            index_list.append([self.__token_to_index(t) for t in token])
        return index_list

    def __sentence_to_token_list(self, sentence):
        token_list = [self.tokenizer(char) for char in sentence]
        return token_list

    def __token_list_to_token_index_list(self, token_list):
        index_list = []
        for token in token_list:
            token = [self.vocab["cls_token"]] + token + [self.vocab["sep_token"]]
            index_list.append([self.__token_to_index(t) for t in token])
        return index_list

    def __sentence_to_token_index_list(self, sentence):
        token_list = self.__sentence_to_token_list(sentence)
        token_index_list = self.__token_list_to_token_index_list(token_list)
        return token_index_list

    def __index_list_to_token_list(self, index_list):
        token_list = []
        for index in index_list:
            token = [self.__index_to_token(i) for i in index]
            token_list.append(token)
        return token_list

    def __token_to_index(self, token):
        if token in self.token_to_index.keys():
            return self.token_to_index[token]
        else:
            token = self.vocab["unk_token"]
            return self.token_to_index[token]            

    def __index_to_token(self, index):
        if index in self.index_to_token.keys():
            return self.index_to_token[index]
        else:
            index = self.token_to_index[self.vocab["unk_token"]]
            return self.index_to_token[index]
        
class BERTClassifier(nn.Module):
    def __init__(self, bert, hidden_size = 768, num_classes=2, dr_rate=None, params=None):
        super(BERTClassifier, self).__init__()
        self.bert = bert
        self.dr_rate = dr_rate                 
        self.classifier = nn.Linear(hidden_size , num_classes)
        if dr_rate:
            self.dropout = nn.Dropout(p=dr_rate)
    
    def gen_attention_mask(self, token_ids, valid_length):
        attention_mask = torch.zeros_like(token_ids)
        for i, v in enumerate(valid_length):
            attention_mask[i][:v] = 1
        return attention_mask.float()

    def forward(self, token_ids, valid_length, segment_ids):
        attention_mask = self.gen_attention_mask(token_ids, valid_length)
        
        _, pooler = self.bert(input_ids = token_ids, token_type_ids = segment_ids.long(), attention_mask = attention_mask.float().to(token_ids.device))
        if self.dr_rate:
            out = self.dropout(pooler)
        return self.classifier(out)
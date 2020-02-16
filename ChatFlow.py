from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import random

import os
import sys
import urllib.request
import json
import datetime

from bs4 import BeautifulSoup 
import urllib

from teanaps.nlp import MorphologicalAnalyzer
from teanaps.nlp import NamedEntityRecognizer
from teanaps.nlp import SyntaxAnalyzer
from teanaps.nlp import Processing
from teanaps.handler import FileHandler
from teanaps.text_analysis import TfidfCalculator

import configure as con

class ChatFlow():  
    def __init__(self):
        self.ma = MorphologicalAnalyzer()
        self.ma.set_tagger("mecab")
        self.ner = NamedEntityRecognizer()
        self.sa = SyntaxAnalyzer()
        self.tfidf = TfidfCalculator()
        self.processing = Processing()
        self.fh = FileHandler()
        self.max_len = 29
        
    def train(self, train_data, file_name):
        self.intent_id_to_name = {}
        intent_name_to_id = {}
        document_list = []
        intent_id = -1
        temp_intent_name = None
        print(len(train_data))
        index = 0
        for query, intent_name in train_data:
            index += 1
            print(index, end="\r")
            if temp_intent_name != intent_name:
                intent_id += 1
            temp_intent_name = intent_name
            self.intent_id_to_name[intent_id] = intent_name
            intent_name_to_id[intent_name] = intent_id
            query_lower = query.lower()
            pos_result = self.ma.parse(query_lower)
            ner_result = self.ner.parse(query_lower)
            sa_result = self.sa.parse(pos_result, ner_result)
            document_list.append(self.processing.get_plain_text(sa_result, tag=False))
            '''
            list_of_input_ids = self.__sentence_to_token_index_list([query_lower])[0]
            input_vector = list_of_input_ids[:self.max_len] + ([0] * (self.max_len-len(list_of_input_ids))) + [list_of_input_ids[-1]]
            document_list.append(input_vector)
            '''
        self.tfidf.calculation_tfidf(document_list)
        tfidf_matrix = self.tfidf.get_tfidf_matrix().values[:]
        label_list = [intent_name_to_id[intent_name] for _, intent_name in train_data]
        x_train, x_test, y_train, y_test = train_test_split(tfidf_matrix, label_list, test_size=0.10, random_state=None)
        #forest = RandomForestClassifier(criterion='entropy', n_estimators=10, random_state=1, n_jobs=2)
        self.intent_model = RandomForestClassifier()
        self.intent_model.fit(x_train, y_train)
        score = self.intent_model.score(x_test, y_test)
        print('Accuracy (forest) :', score)
        self.fh.save_data(file_name, self.intent_model)
        self.fh.save_data("intent_id_to_name", self.intent_id_to_name)
        print("Model Saved.", file_name)
        self.load_vectorizer("tfidf_vectorizer")
    
    def load_model(self, file_name):
        self.intent_model = self.fh.load_data(file_name)
        print("Model Loaded.", file_name)
        self.intent_id_to_name = self.fh.load_data("intent_id_to_name")
    
    def load_vectorizer(self, file_name):
        self.vectorizer = self.fh.load_data(file_name)
        print("Vectorizer Loaded.", file_name)
        self.intent_id_to_name = self.fh.load_data("intent_id_to_name")
        
    def get_intent(self, flow, query, max_intent_count=1, intent_th=0):
        # Query to Vector
        query_lower = query.lower()
        pos_result = self.ma.parse(query_lower)
        ner_result = self.ner.parse(query_lower)
        sa_result = self.sa.parse(pos_result, ner_result)
        input_vector = self.tfidf.get_tfidf_vector(self.processing.get_plain_text(sa_result, tag=False))
        '''
        list_of_input_ids = self.__sentence_to_token_index_list([query_lower])[0]
        input_vector = list_of_input_ids[:self.max_len] + ([0] * (self.max_len-len(list_of_input_ids))) + [list_of_input_ids[-1]]
        '''
        # Predict Intent
        intent_prob_list = self.intent_model.predict_proba([input_vector]).tolist()[0]
        intent_list = [(self.intent_id_to_name[i], i, r) for i, r in enumerate(intent_prob_list) if r > intent_th]
        intent_list.sort(key=lambda elem: elem[2], reverse=True)
        query_info_list = []
        for intent_no, intent in enumerate(intent_list[:max_intent_count]):
            flow.set_query(query)
            flow.set_status("get_intent")
            flow.set_intent_type(intent_no, intent[0])
            flow.set_probability(intent_no, intent[2])

    def get_meta(self, flow):
        flow.set_status("get_meta")
        flow = flow.get_flow()
        query = flow["query"]
        pos_result = self.ma.parse(query)
        ner_result = self.ner.parse(query)
        sa_result = self.sa.parse(pos_result, ner_result)
        for intent in flow["intent"]:
            intent["meta"] = {}
            intent["sub_meta"] = []
            for meta in con.META_FOR_INTENT[intent["intent_type"]]:
                meta_tag = con.NER_FOR_META[meta]
                intent["meta"][meta] = []
                for word, pos_tag, ner_tag, loc in sa_result:
                    if ner_tag in meta_tag:
                        intent["meta"][meta].append(word)
                    elif pos_tag in ["NNG", "NNP", "MAG"] and word not in intent["sub_meta"]:
                        intent["sub_meta"].append(word)
                        
    def check_meta(self, flow, intent_no):
        flow.set_status("check_meta")
        flow = flow.get_flow()
        intent = flow["intent"][intent_no]
        if sum([len(intent["meta"][key]) for key in intent["meta"].keys()]) == 0:
            if len(intent["meta"].keys()) > 0:
                question = con.QUERY_FOR_META[list(intent["meta"].keys())[0]]
                self.ask_a_question(question)
                return False
        return True
    
    def ask_a_question(self, question):
        print("Chat-bot :", question)
        
    def get_user_response(self, flow, intent_no, user_response):
        flow.set_status("user_response")
        flow = flow.get_flow()
        intent = flow["intent"][intent_no]
        intent["meta"][list(intent["meta"].keys())[0]].append(user_response)      

    def get_answer(self, flow, intent_no):
        flow.set_status("get_answer")
        flow = flow.get_flow()
        intent = flow["intent"][intent_no]
        answer = random.choice(con.REPLY_CANDIDATE[intent["intent_type"]])
        print(intent["meta"].keys())
        meta = intent["meta"][list(intent["meta"].keys())[0]][0]
        intent["answer"] = answer.replace("{1}", meta)
        if intent["intent_type"] in ["news", "issue"]:
            intent["answer"] += "\n------\n" + self.find_news(meta, "news")
        elif intent["intent_type"] in ["information"]:
            intent["answer"] += "\n------\n" + self.find_news(meta, "blog")
        elif intent["intent_type"] in ["people"]:
            intent["answer"] += "\n------\n" + self.get_people_info(meta)
        elif intent["intent_type"] in ["music"]:
            intent["answer"] += "\n------\n링크에서 정보를 확인해보세요.\nhttps://vibe.naver.com/search?query=" + meta
        elif intent["intent_type"] in ["weather", "dust"]:
            intent["answer"] += "\n------\n" + self.get_weather_info(meta)
        elif intent["intent_type"] in ["restraunt", "saying", "nonsense"]:
            intent["answer"] += "\n------\n" + self.find_news(meta, "blog")
        elif intent["intent_type"] in ["time", "date"]:
            now = datetime.datetime.now()
            date_time = now.strftime('%Y년 %m월 %d일 %H시 %M분 %S초')
            intent["answer"] += "\n------\n" + date_time
        elif intent["intent_type"] in ["transfer"]:
            intent["answer"] += "\n------\n" + "준비중"
        elif intent["intent_type"] in ["translate"]:
            intent["answer"] += "\n------\n" + self.translate(intent["query"])
            
    def translate(self, query, language="en"):
        if query.strip() == "":
            return "번역할 수 없습니다."
        encText = urllib.parse.quote(query)
        data = "source=ko&target=" + language + "&text=" + encText
        url = "https://openapi.naver.com/v1/papago/n2mt"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", con.NAVER_API_CID)
        request.add_header("X-Naver-Client-Secret", con.NAVER_API_CPW)
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        rescode = response.getcode()
        if(rescode==200):
            response_body = response.read()
            translated_text = json.loads(response_body.decode('utf-8'))["message"]["result"]["translatedText"]
            return translated_text
        else:
            return "Error Code:" + rescode        
    
    def find_news(self, query, source):
        if query.strip() == "":
            return "정보를 찾을 수 없습니다."
        encText = urllib.parse.quote(query)
        url = "https://openapi.naver.com/v1/search/" + source + "?query=" + encText # json 결과
        # url = "https://openapi.naver.com/v1/search/blog.xml?query=" + encText # xml 결과
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", con.NAVER_API_CID)
        request.add_header("X-Naver-Client-Secret", con.NAVER_API_CPW)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        if(rescode==200):
            response_body = response.read()
            items = json.loads(response_body.decode('utf-8'))["items"]
            result = ""
            for i, item in enumerate(items):
                result += str(i) + ".\n"
                result += item["title"] + "\n"
                result += item["link"] + "\n\n"
            return result
        else:
            return "Error Code:" + rescode
    
    def get_people_info(self, query):
        query = urllib.parse.quote(query)
        URL = "https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query=" + query
        page = urllib.request.urlopen(URL)
        soup = BeautifulSoup(page, "html.parser")
        people_info = soup.find("dl", {'class': "detail_profile",})
        name = people_info.find("dd", {'class': "name",}).find("a").text
        link = people_info.find("dd", {'class': "name",}).find("a")["href"]
        job = people_info.find("dd", {'class': "name",}).find_all("span")[-1].text
        info = {
            "name": name,
            "job": job
        }
        for label, content in zip(people_info.find_all("dt"), people_info.find_all("dd")[1:]):
            info[label.text] = content.text
        info["link"] = link
        result = ""
        for k, v in info.items():
            result += k + " : " + v + "\n"
        return result.strip()
    
    def get_weather_info(self, query):
        query_string = urllib.parse.quote(query)
        URL = "https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query=" + query_string + "+%EB%82%A0%EC%94%A8"
        page = urllib.request.urlopen(URL)
        soup = BeautifulSoup(page, "html.parser")
        weather_box = soup.find("div", {'class': "weather_box",})
        result = ""
        temp = weather_box.find("span", {'class': "todaytemp",}).text + "도"
        desc = weather_box.find("p", {'class': "cast_txt",}).text
        result += query + " 날씨는" + temp + "로, " + desc + "."
        status = weather_box.find("dl", {'class': "indicator",}).find_all("dd")
        label = weather_box.find("dl", {'class': "indicator",}).find_all("dt")
        for s, l in zip(status, label):
            result += l.text + "는 " + s.text[-2:] + " "
        result += "입니다."
        return result

    def __sentence_to_token_index_list(self, sentence):
        token_list = self.__sentence_to_token_list(sentence)
        token_index_list = self.__token_list_to_token_index_list(token_list)
        return token_index_list

    def __sentence_to_token_list(self, sentence):
        token_list = [self.ner.tokenizer(char) for char in sentence]
        return token_list

    def __token_list_to_token_index_list(self, token_list):
        index_list = []
        for token in token_list:
            token = [self.ner.vocab["cls_token"]] + token + [self.ner.vocab["sep_token"]]
            token = [self.ner.vocab["cls_token"]] + token + [self.ner.vocab["sep_token"]]
            index_list.append([self.__token_to_index(t) for t in token])
        return index_list

    def __token_to_index(self, token):
        if token in self.ner.token_to_index.keys():
            return self.ner.token_to_index[token]
        else:
            token = self.ner.vocab["unk_token"]
            return self.ner.token_to_index[token]
        
class Flow():
    def __init__(self, intent_count):
        intent = {
            "intent_type": None,
            "probability": 0.0,
            "meta": {},
            "sub_meta": [],
            "answer": None
        }
        self.flow = {
            "query": None,
            "status": "ready",
            "intent": [intent] * intent_count
        }
        
    def get_flow(self):
        return self.flow
    
    def init_meta(self, intent_no):
        for meta_type in self.flow["intent"][intent_no]["meta"].keys():
            self.flow["intent"][intent_no]["meta"][meta_type] = []
    
    def set_query(self, query):
        self.flow["query"] = query
    
    def set_intent_type(self, intent_no, intent_type):
        self.flow["intent"][intent_no]["intent_type"] = intent_type
    
    def set_status(self, status):
        self.flow["status"] = status
    
    def set_probability(self, intent_no, probability):
        self.flow["intent"][intent_no]["probability"] = probability
    
    def set_meta(self, intent_no, meta_type, meta):
        self.flow["intent"][intent_no]["meta"] = {}
        self.flow["intent"][intent_no]["meta"][meta_type] = meta
    
    def add_sub_meta(self, intent_no, sub_meta):
        self.flow["intent"][intent_no]["sub_meta"].append(sub_meta)
        
    def set_answer(self, intent_no, answer):
        self.flow["intent"][intent_no]["answer"] = answer
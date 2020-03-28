from teanaps.nlp import MorphologicalAnalyzer
from teanaps.nlp import NamedEntityRecognizer
from teanaps.nlp import SyntaxAnalyzer
from teanaps.nlp import Processing
from teanaps.handler import FileHandler
from teanaps.text_analysis import TfidfCalculator

import configure as con
from flow_manager import SkillHandler
from flow_manager import IntentClassifier
from flow_manager import DialogflowHandler

import datetime
import random

class FlowHandler():  
    def __init__(self):
        self.ma = MorphologicalAnalyzer()
        self.ma.set_tagger("mecab")
        self.ner = NamedEntityRecognizer()
        self.sa = SyntaxAnalyzer()
        self.tfidf = TfidfCalculator()
        self.processing = Processing()
        self.fh = FileHandler()
        self.sh = SkillHandler()
        self.model_type = "random_forest"
    
    def load_model(self, model_type="random_forest"):
        if model_type == "random_forest":    
            self.intent_model = self.fh.load_data(con.MODEL_CONFIG["random_forest"]["model"])
            self.intent_id_to_name = self.fh.load_data(con.MODEL_CONFIG["random_forest"]["intent_id_to_name"])
        elif model_type == "bert":
            self.ic = IntentClassifier.IntentClassifierBERT()
        elif model_type == "dialogflow":
            self.dm = DialogflowHandler()
        self.model_type = model_type
               
    def get_intent(self, flow, query, max_intent_count=1, intent_th=0):
        flow.set_status("get_intent")
        flow.set_query(query)
        query_lower = query.lower()
        if self.model_type == "random_forest":
            # Query to Vector
            pos_result = self.ma.parse(query_lower)
            ner_result = self.ner.parse(query_lower)
            sa_result = self.sa.parse(pos_result, ner_result)
            input_vector = self.tfidf.get_tfidf_vector(self.processing.get_plain_text(sa_result, tag=False), tfidf_vectorizer_path=con.MODEL_CONFIG["random_forest"]["vectorizer"])
            # Predict Intent
            intent_prob_list = self.intent_model.predict_proba([input_vector]).tolist()[0]
            intent_list = [(self.intent_id_to_name[i], i, r) for i, r in enumerate(intent_prob_list) if r > intent_th]
            intent_list.sort(key=lambda elem: elem[2], reverse=True)
            for intent_no, intent in enumerate(intent_list[:max_intent_count]):
                flow.set_intent_type(intent_no, intent[0])
                flow.set_probability(intent_no, intent[2])
                flow.set_nlu_type(intent_no, "machine-learning")
        elif self.model_type == "bert":
            intent_prob_list = self.ic.parse(query_lower, intent_count=max_intent_count)
            intent_list = [(intent_type, intent_prob) for intent_type, intent_prob in intent_prob_list if intent_prob > intent_th]
            for intent_no, intent in enumerate(intent_list[:max_intent_count]):
                flow.set_intent_type(intent_no, intent[0])
                flow.set_probability(intent_no, intent[1])
                flow.set_nlu_type(intent_no, "deep-learning")
        elif self.model_type == "dialogflow":
            intent = self.dm.get_intent(query_lower)
            flow.set_intent_type(0, intent[0])
            flow.set_probability(0, intent[1])
            flow.set_nlu_type(0, "dialogflow")
            
    def select_intent(self, flow, intent_no):
        flow["intent"] = [flow["intent"][intent_no]]
                  
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
                for word, pos_tag, ner_tag, _ in sa_result:
                    if ner_tag in meta_tag:
                        intent["meta"][meta].append(word)
                    elif pos_tag in ["NNG", "NNP", "MAG"]:
                        if word in con.META_FOR_META_TYPE.keys():
                            if con.META_FOR_META_TYPE[word] in intent["meta"].keys():
                                if word not in intent["meta"][con.META_FOR_META_TYPE[word]]:
                                    intent["meta"][con.META_FOR_META_TYPE[word]].append(word)
                        else:
                            if word not in intent["sub_meta"]:
                                intent["sub_meta"].append(word)
     
    def check_meta(self, flow):
        flow = flow.get_flow()
        check_list = []
        for intent in flow["intent"]:
            if intent["intent_type"] in ["time", "date"]:
                if sum([len(intent["meta"][key]) for key in intent["meta"].keys()]) == 0:
                    intent["meta"]["when"].append(None)
                    check_list.append(True)
                    continue
            elif intent["intent_type"] in ["weather", "dust"]:
                if sum([len(intent["meta"][key]) for key in intent["meta"].keys()]) == 0:
                    intent["meta"]["when"].append("오늘")
                    check_list.append(True)
                    continue
            elif intent["intent_type"] in ["translate"]:
                if sum([len(intent["meta"][key]) for key in intent["meta"].keys()]) == 0:
                    intent["meta"]["language"].append("영어")
                    check_list.append(True)
                    continue
            if sum([len(intent["meta"][key]) for key in intent["meta"].keys()]) == 0:
                if len(intent["meta"].keys()) > 0:
                    check_list.append(False)
                    continue 
            check_list.append(True)
            continue
        return check_list
                                       
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
        if intent["intent_type"] in ["news", "issue"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            result_list = self.sh.find_news(meta)
            intent["answer"] = result_list
        elif intent["intent_type"] in ["information"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            result_list = self.sh.find_blog(meta)
            intent["answer"] = result_list
        elif intent["intent_type"] in ["people"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            result = self.sh.get_people_info(meta)
            intent["answer"].append(result)
        elif intent["intent_type"] in ["music"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            answer_dict = {"text": answer.replace("{1}", meta), "link": "https://vibe.naver.com/search?query=" + meta}
            intent["answer"].append(answer_dict)
        elif intent["intent_type"] in ["weather", "dust"]:
            when = intent["meta"]["when"][0] if len(intent["meta"]["when"]) > 0 else None
            location = intent["meta"]["location"][0] if len(intent["meta"]["location"]) > 0 else None
            text = self.sh.get_weather_info(when, location)
            answer_dict = {"text": text, "link": None}
            intent["answer"].append(answer_dict)
        elif intent["intent_type"] in ["restraunt", "saying", "nonsense"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            result_list = self.sh.find_blog(meta)
            intent["answer"] = result_list
        elif intent["intent_type"] in ["time", "date"]:
            if len(intent["meta"][list(intent["meta"].keys())[0]]) == 0:
                answer_dict = {"text": text, "link": None}
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            now = datetime.datetime.now()
            if intent["intent_type"] == "time":
                date_time = now.strftime('%Y년 %m월 %d일 %H시 %M분 %S초')
                text = "현재 시간은 " + date_time + "입니다."
            else:
                date_time = now.strftime('%Y년 %m월 %d일')
                text = "오늘은 " + date_time + "입니다."
            answer_dict = {"text": text, "link": None}
            intent["answer"].append(answer_dict)
        elif intent["intent_type"] in ["transfer"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            text = answer.replace("{1}", meta) + "\n------\n" + "준비중"
            answer_dict = {"text": text, "link": None}
            intent["answer"].append(answer_dict)
        elif intent["intent_type"] in ["translate"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            text = answer + "\n" + meta + ") " + self.sh.translate(flow["query"], language=meta)
            answer_dict = {"text": text, "link": None}
            intent["answer"].append(answer_dict)
 
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
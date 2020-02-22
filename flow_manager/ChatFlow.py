from teanaps.nlp import MorphologicalAnalyzer
from teanaps.nlp import NamedEntityRecognizer
from teanaps.nlp import SyntaxAnalyzer
from teanaps.nlp import Processing
from teanaps.handler import FileHandler
from teanaps.text_analysis import TfidfCalculator

from flow_manager import configure as con

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

from bs4 import BeautifulSoup 
import urllib.request
import datetime
import random
import json
import copy

class ChatFlow():  
    def __init__(self):
        self.ma = MorphologicalAnalyzer()
        self.ma.set_tagger("mecab")
        self.ner = NamedEntityRecognizer()
        self.sa = SyntaxAnalyzer()
        self.tfidf = TfidfCalculator()
        self.processing = Processing()
        self.fh = FileHandler()
        
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
        self.load_vectorizer()
    
    def load_model(self):        
        self.intent_model = self.fh.load_data(con.INTENT_MODEL_PATH)
        self.intent_id_to_name = self.fh.load_data(con.INTENT_UTIL_PATH["intent_id_to_name"])
    
    def load_vectorizer(self):
        self.vectorizer = self.fh.load_data(con.INTENT_UTIL_PATH["tfidf_vectorizer"])
        self.intent_id_to_name = self.fh.load_data(con.INTENT_UTIL_PATH["intent_id_to_name"])
        
    def get_intent(self, flow, query, max_intent_count=1, intent_th=0):
        flow.set_status("get_intent")
        flow.set_query(query)
        # Query to Vector
        query_lower = query.lower()
        pos_result = self.ma.parse(query_lower)
        ner_result = self.ner.parse(query_lower)
        sa_result = self.sa.parse(pos_result, ner_result)
        input_vector = self.tfidf.get_tfidf_vector(self.processing.get_plain_text(sa_result, tag=False), tfidf_vectorizer_path=con.TFIDF_VECTORIZER_PATH)
        # Predict Intent
        intent_prob_list = self.intent_model.predict_proba([input_vector]).tolist()[0]
        intent_list = [(self.intent_id_to_name[i], i, r) for i, r in enumerate(intent_prob_list) if r > intent_th]
        intent_list.sort(key=lambda elem: elem[2], reverse=True)
        for intent_no, intent in enumerate(intent_list[:max_intent_count]):
            flow.set_intent_type(intent_no, intent[0])
            flow.set_probability(intent_no, intent[2])
     
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
            result_list = self.find_news(meta)
            intent["answer"] = result_list
        elif intent["intent_type"] in ["information"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            result_list = self.find_blog(meta)
            intent["answer"] = result_list
        elif intent["intent_type"] in ["people"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            result = self.get_people_info(meta)
            intent["answer"].append(result)
        elif intent["intent_type"] in ["music"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            answer_dict = {"text": answer.replace("{1}", meta), "link": "https://vibe.naver.com/search?query=" + meta}
            intent["answer"].append(answer_dict)
        elif intent["intent_type"] in ["weather", "dust"]:
            when = intent["meta"]["when"][0] if len(intent["meta"]["when"]) > 0 else None
            location = intent["meta"]["location"][0] if len(intent["meta"]["location"]) > 0 else None
            text = self.get_weather_info(when, location)
            answer_dict = {"text": text, "link": None}
            intent["answer"].append(answer_dict)
        elif intent["intent_type"] in ["restraunt", "saying", "nonsense"]:
            meta = intent["meta"][list(intent["meta"].keys())[0]][0]
            result_list = self.find_blog(meta)
            intent["answer"] = result_list
        elif intent["intent_type"] in ["time", "date"]:
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
            text = answer + "\n" + meta + ") " + self.translate(flow["query"], language=meta)
            answer_dict = {"text": text, "link": None}
            intent["answer"].append(answer_dict)
            
    def translate(self, query, language="영어"):
        if language not in con.LANGUAGE_TO_CODE.keys():
            return "지원하지 않는 언어입니다."
        language_code = con.LANGUAGE_TO_CODE[language]
        query_lower = query.lower()
        pos_result = self.ma.parse(query_lower)
        ner_result = self.ner.parse(query_lower)
        sa_result = self.sa.parse(pos_result, ner_result)
        end = -1
        for i, sa in enumerate(sa_result):
            if sa[0] in [key for key in con.META_FOR_META_TYPE.keys() if con.META_FOR_META_TYPE[key] == "language"]:
                if sa_result[i-1][1] in ["JKS"]:
                    sa_result[i-1][3][0]
                else:  
                    end = sa[3][0]
                break
            end = sa[3][0]
        query = query[:end]
        if query.strip() == "":
            return "번역할 수 없는 문장입니다."
        encText = urllib.parse.quote(query)
        data = "source=ko&target=" + language_code + "&text=" + encText
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
            return "번역할 수 없는 문장입니다."        
    
    def find_news(self, query):
        if query.strip() == "":
            return []
        encText = urllib.parse.quote(query)
        url = "https://openapi.naver.com/v1/search/news?query=" + encText
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", con.NAVER_API_CID)
        request.add_header("X-Naver-Client-Secret", con.NAVER_API_CPW)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        result_list = []        
        if(rescode==200):
            response_body = response.read()
            items = json.loads(response_body.decode('utf-8'))["items"]
            for item in items[:5]:
                thumbnail_image = self.get_news_thumbnail_image(item["link"])
                result_list.append({"text": self.remove_html(item["title"]), 
                                    "link": item["link"],
                                    "thumbnail_image": thumbnail_image,
                                    "desc": self.remove_html(item["description"])})
            return result_list
        else:
            return []
        
    def find_blog(self, query):
        if query.strip() == "":
            return []
        encText = urllib.parse.quote(query)
        url = "https://search.naver.com/search.naver?where=post&sm=tab_jum&query=" + encText
        page = urllib.request.urlopen(url)
        soup = BeautifulSoup(page, "html.parser")       
        title_list = [post["title"] for post in soup.find_all("a", {'class': "sh_blog_title",})][:5]
        link_list = [post["href"] for post in soup.find_all("a", {'class': "sh_blog_title",})][:5]
        desc_list = [post.text for post in soup.find_all("dd", {'class': "sh_blog_passage",})][:5]
        thumbnail_list = [img["src"] for img in soup.find_all("img", {'class': "sh_blog_thumbnail",})][:5]
        blog_list = []
        for title, link, desc, thumbnail in zip(title_list, link_list, desc_list, thumbnail_list):
            blog_list.append({"text": title, "link": link, "desc": desc, "thumbnail_image": thumbnail})
        return blog_list
    
    def remove_html(self, text):
        html_code_list = ["&nbsp;", "&quot;", "&amp;", "&apos;", "&lt;", "&gt;", "&nbsp;", "&iexcl;", 
                          "&cent;", "&pound;", "&curren;", "&yen;", "&brvbar;", "&sect;", "&uml;", 
                          "&copy;", "&ordf;", "&laquo;", "&not;", "</b>", "<b>"]
        for html_code in html_code_list:
            if html_code in ["<b>", "</b>", "&quot;"]:
                text = text.replace(html_code, "\"")
            else:
                text = text.replace(html_code, "")
        return text
    
    def get_news_thumbnail_image(self, url):
        try:
            page = urllib.request.urlopen(url)
            soup = BeautifulSoup(page, "html.parser")
            return soup.find("meta", {'property': "og:image",})["content"]
        except:
            return "https://github.com/fingeredman/chatbot-with-teanaps/blob/master/data/logo/teanaps_chatbot_logo_square.png"
        
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
        result = {}
        text = ""
        for k, v in info.items():
            text += "▷ " + k.replace("name", "이름").replace("job", "직업") + " : " + v + "\n"
        result["text"] = text.strip()
        result["link"] = link
        return result
    
    def get_weather_info(self, when, location):
        query = ""
        if when is not None:
            query += when + " "
        if location is not None:
            query += location + " "
        query_string = urllib.parse.quote(query)
        URL = "https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query=" + query_string + "+%EB%82%A0%EC%94%A8"
        page = urllib.request.urlopen(URL)
        soup = BeautifulSoup(page, "html.parser")
        weather_box = soup.find("div", {'class': "weather_box",})
        result = ""
        temp = weather_box.find("span", {'class': "todaytemp",}).text + "도"
        desc = weather_box.find("p", {'class': "cast_txt",}).text
        result += query + "날씨는" + temp + "로, " + desc + ". "
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
            "answer": []
        }
        self.flow = {
            "query": None,
            "reply_query": [],
            "status": "ready",
            "intent": []
        }
        for i in range(intent_count):
            self.flow["intent"].append(copy.deepcopy(intent))
        
    def get_flow(self):
        return self.flow
    
    def init_meta(self):
        for intent in self.flow["intent"]:
            for meta_type in intent["meta"].keys():
                intent["meta"][meta_type] = []
            intent["answer"] = []
            self.flow["status"] = "ready"
    
    def add_reply_query(self, query):
        self.flow["reply_query"].append(query)
        
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

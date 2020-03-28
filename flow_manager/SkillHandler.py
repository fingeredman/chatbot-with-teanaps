from teanaps.nlp import MorphologicalAnalyzer
from teanaps.nlp import NamedEntityRecognizer
from teanaps.nlp import SyntaxAnalyzer

import configure as con

from bs4 import BeautifulSoup 
import urllib.request
import json

class SkillHandler():  
    def __init__(self):
        self.ma = MorphologicalAnalyzer()
        self.ma.set_tagger("mecab")
        self.ner = NamedEntityRecognizer()
        self.sa = SyntaxAnalyzer()
    
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
        try:
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
        except:
            result = {}            
            result["text"] = "인물정보를 찾을 수 없습니다."
            result["link"] = None
        return result
    
    def get_weather_info(self, when, location):
        query = ""
        if when is not None:
            query += when + " "
        if location is not None:
            query += location + " "
        try:
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
        except:
            result = "날씨정보를 찾을 수 없습니다."
        return result
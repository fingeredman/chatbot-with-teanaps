REPLY_TYPE = {
    "simple_text": {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleText": {
                    "text": None
                }}],
            "quickReplies":[]
        }
    },
    "carousel": {
        "version": "2.0",
        "template": {
            "outputs": []
        }
    },
    "list_card": {
        "version": "2.0",
        "template": {
            "outputs": []
        }
    }
}
TFIDF_VECTORIZER_PATH = "../model/intent/tfidf_vectorizer"
INTENT_MODEL_PATH = "../model/intent/intent_model_v1"
INTENT_UTIL_PATH = {
    "intent_id_to_name": "../model/intent/intent_id_to_name",
    "tfidf_vectorizer": "../model/intent/tfidf_vectorizer",
}
META_FOR_META_TYPE = {
    "오늘": "when",
    "내일": "when",
    "모레": "when",
    "어제": "when",
    "그저께": "when",
    "지금": "when",
    "영어": "language",
    "미국말": "language",
    "중국어": "language",
    "스페인어": "language",
    "한국어": "language",
    "한국말": "language",
    "불어": "language",
    "프랑스어": "language",
    "베트남어": "language",
    "태국어": "language",
    "인도네시아어": "language",
    "번역": "language"
}
LANGUAGE_TO_CODE = {
    "영어": "en",
    "미국말": "en",
    "중국어": "zh-CN",
    "스페인어": "es",
    "한국어": "ko",
    "한국말": "ko",
    "불어": "fr",
    "프랑스어": "fr",
    "베트남어": "vi",
    "태국어": "th",
    "인도네시아어": "id",
    "번역": "en"
}
META_FOR_INTENT = {
    #"nonsense": [],
    "information": ["about"],
    "music": ["singer", "title"],
    "issue": ["when", "category"],
    "people": ["who"],
    "transfer": ["player", "team"],
    "date": ["when"],
    "weather": ["when", "location"],
    "news": ["about"],
    "restraunt": ["location"],
    "dust": ["when", "location"],
    #"saying": [],
    "translate": ["language"],
    "time": ["when"],
}
NER_FOR_META = {
    "about": ["PS", "FD", "TR", "AF", "OG", "LC", "CV", "EV", "AM", "PT", "MT", "TM"],
    "singer": ["PS", "OG"],
    "title": [],
    "when": ["DT", "TI"],
    "category": [],
    "who": ["PS", "OG"],
    "player": ["PS"],
    "team": ["OG"],
    "location": ["LC"],
    "language": []
}
QUERY_FOR_META = {
    "about": "뭘?",
    "singer": "누구노래?",
    "title": "제목은?",
    "when": "언제?",
    "category": "어느분야?",
    "who": "누구?",
    "player": "어떤선수?",
    "team": "어느팀?",
    "location": "어디?",
    "language": "어느나라 말로?"
}
REPLY_CANDIDATE = {
    "nonsense": ["정답은 \"{1}\" 입니다."],
    "information": ["말씀하신 내용을 찾아봤어요."],
    "music": ["\"{1}\" 노래를 찾아봤어요."],
    "issue": ["\"{1}\" 이슈를 찾아봤어요."],
    "people": ["\"{1}\" 인물정보를 찾았습니다."],
    "transfer": ["\"{1}\" 이적정보를 알려드립니다."],
    "date": ["\"{1}\" 날짜를 알려드려요."],
    "weather": ["날씨예보입니다."],
    "news": ["요청하신 뉴스를 찾았습니다."],
    "restraunt": ["말씀하진 지역 맛집을 찾아봤어요."],
    "dust": ["\"{1}\" 미세먼지 예보입니다."],
    "saying": ["글귀 하나를 추천드려요."],
    "translate": ["번역 결과입니다."],
    "time": ["\"{1}\" 시간을 알려드려요."],
}
NAVER_API_CID = "BaR------"
NAVER_API_CPW = "3_q------"

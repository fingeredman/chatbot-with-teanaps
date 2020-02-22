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
    None: []
}
META_ID_TO_NAME = {
    "information": "정보 물어보기",
    "music": "음악/가수 정보 물어보기",
    "issue": "이슈 물어보기",
    "people": "인물정보 물어보기",
    "transfer": "이적시장 물어보기",
    "date": "날짜 물어보기",
    "weather": "날씨 물어보기",
    "news": "뉴스 찾아보기",
    "restraunt": "맛집 물어보기",
    "dust": "미세먼지 정보 물어보기",
    "translate": "번역 물어보기",
    "time": "시간 물어보기"
}
META_NAME_TO_ID = {
    "정보 물어보기": "information",
    "음악/가수 정보 물어보기": "music",
    "이슈 물어보기": "issue",
    "인물정보 물어보기": "people",
    "이적시장 물어보기": "transfer",
    "날짜 물어보기": "date",
    "날씨 물어보기": "weather",
    "뉴스 찾아보기": "news",
    "맛집 물어보기": "restraunt",
    "미세먼지 정보 물어보기": "dust",
    "번역 물어보기": "translate",
    "시간 물어보기": "time"
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
    "about": "무엇에 대해 찾으시나요?",
    "singer": "누구 노래,또는 어떤 노래를 찾으시나요?",
    "title": "제목을 알려주실 수 있나요?",
    "when": "언제 정보를 가져올까요?",
    "category": "어느분야 정보가 필요하세요?",
    "who": "누구 정보를 찾으세요?",
    "player": "어떤 선수 정보를 찾으시나요?",
    "team": "어느팀 정보를 찾으시나요?",
    "location": "어디를 말씀하시는거에요?",
    "language": "어느나라 말로 번역할까요?"
}
REPLY_CANDIDATE = {
    "nonsense": ["정답은 \"{1}\" 입니다."],
    "information": ["말씀하신 내용을 찾아봤어요."],
    "music": ["노래를 찾아봤어요."],
    "issue": ["이슈를 찾아봤어요."],
    "people": ["인물정보를 찾았습니다."],
    "transfer": ["이적정보를 알려드립니다."],
    "date": ["날짜를 알려드려요."],
    "weather": ["날씨예보입니다."],
    "news": ["요청하신 뉴스를 찾았습니다."],
    "restraunt": ["말씀하진 지역 맛집을 찾아봤어요."],
    "dust": ["미세먼지 예보입니다."],
    "saying": ["글귀 하나를 추천드려요."],
    "translate": ["번역 결과입니다."],
    "time": ["시간을 알려드려요."],
}
NAVER_API_CID = "BaR------"
NAVER_API_CPW = "3_q------"

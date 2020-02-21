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
    "information": ["\"{1}\" 관련 정보를 찾아드릴게요."],
    "music": ["\"{1}\" 노래를 찾아봤어요."],
    "issue": ["\"{1}\" 이슈를 찾아봤어요."],
    "people": ["\"{1}\" 인물정보를 찾았습니다."],
    "transfer": ["\"{1}\" 이적정보를 알려드립니다."],
    "date": ["\"{1}\" 날짜를 알려드려요."],
    "weather": ["\"{1}\" 날씨예보입니다."],
    "news": ["\"{1}\" 관련 뉴스를 찾았습니다."],
    "restraunt": ["\"{1}\" 주변 맛집을 찾아봤어요."],
    "dust": ["\"{1}\" 미세먼지 예보입니다."],
    "saying": ["글귀 하나를 추천드려요."],
    "translate": ["\"{1}\" 번역 결과입니다."],
    "time": ["\"{1}\" 시간을 알려드려요."],
}
NAVER_API_CID = "###"
NAVER_API_CPW = "###"

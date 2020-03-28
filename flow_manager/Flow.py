import copy

class Flow():
    def __init__(self, intent_count):
        intent = {
            "intent_type": None,
            "probability": 0.0,
            "nlu_type": "kakao open builder i",
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
            intent["sub_meta"] = []
            intent["answer"] = []
            self.flow["status"] = "ready"
    
    def add_reply_query(self, query):
        self.flow["reply_query"].append(query)
        
    def set_query(self, query):
        self.flow["query"] = query
    
    def set_intent_type(self, intent_no, intent_type):
        self.flow["intent"][intent_no]["intent_type"] = intent_type
        
    def set_nlu_type(self, intent_no, nlu_type):
        self.flow["intent"][intent_no]["nlu_type"] = nlu_type
        
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
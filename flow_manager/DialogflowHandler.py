import dialogflow_v2 as dialogflow

from flow_manager import configure as con

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = con.DIALOGFLOW_CREDENTIAL_PATH

class DialogflowHandler():  
    def __init__(self):
        self.base_url = con.DIALOGFLOW_BASE_URL
        self.client_access_token = con.DIALOGFLOW_CLIENT_ACCESS_TOKEN
        self.developer_access_token = con.DIALOGFLOW_DEVELOPER_ACCESS_TOKEN
        self.project_id = con.DIALOGFLOW_PROJECT_ID
        self.language_code = con.DIALOGFLOW_LANGUAGE_CODE
        self.session_id = con.DIALOGFLOW_SESSTION_ID
    
    def detect_intent_texts(self, sentence):
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(self.project_id, self.session_id)
        text_input = dialogflow.types.TextInput(text=sentence, language_code=self.language_code)
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session, query_input=query_input)
        return (response.query_result.intent.display_name, response.query_result.intent_detection_confidence, response.query_result.fulfillment_text)
       
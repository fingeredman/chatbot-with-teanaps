import dialogflow_v2 as dialogflow

from flow_manager import configure as con

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = con.DIALOGFLOW_CREDENTIAL_PATH

class DialogflowHandler():  
    def __init__(self, base_url = con.DIALOGFLOW_BASE_URL,
                 client_access_token = con.DIALOGFLOW_CLIENT_ACCESS_TOKEN,
                 developer_access_token = con.DIALOGFLOW_DEVELOPER_ACCESS_TOKEN,
                 project_id = con.DIALOGFLOW_PROJECT_ID,
                 language_code = con.DIALOGFLOW_LANGUAGE_CODE,
                 session_id = con.DIALOGFLOW_SESSTION_ID):
        self.base_url = base_url
        self.client_access_token = client_access_token
        self.developer_access_token = developer_access_token
        self.project_id = project_id
        self.language_code = language_code
        self.session_id = session_id
    
    def get_intent(self, sentence):
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(self.project_id, self.session_id)
        text_input = dialogflow.types.TextInput(text=sentence, language_code=self.language_code)
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session, query_input=query_input)
        intent_type = response.query_result.intent.display_name
        probability = response.query_result.intent_detection_confidence
        response = response.query_result.fulfillment_text
        return (intent_type, probability, response)
    
    def create_intent(self, intent_type, train_sentence_list, response_sentence_list):
        intents_client = dialogflow.IntentsClient()
        parent = intents_client.project_agent_path(self.project_id)
        training_phrases = []
        for training_phrases_part in train_sentence_list:
            part = dialogflow.types.Intent.TrainingPhrase.Part(text=training_phrases_part)
            training_phrase = dialogflow.types.Intent.TrainingPhrase(parts=[part])
            training_phrases.append(training_phrase)
        text = dialogflow.types.Intent.Message.Text(text=response_sentence_list)
        message = dialogflow.types.Intent.Message(text=text)
        intent = dialogflow.types.Intent(display_name=intent_type, training_phrases=training_phrases, messages=[message])
        intents_client.create_intent(parent, intent)
        
    def get_intent_list(self):
        intent_list = []
        intents_client = dialogflow.IntentsClient()
        parent = intents_client.project_agent_path(self.project_id)
        intents = intents_client.list_intents(parent)
        for intent in intents:
            intent_id = intent.name.split("/intents/")[1]
            intent_type = intent.display_name
            intent_list.append([intent_id, intent_type])
        return intent_list
       
    def delete_intent(self, intent_id):
        intents_client = dialogflow.IntentsClient()
        intent_path = intents_client.intent_path(self.project_id, intent_id)
        intents_client.delete_intent(intent_path)
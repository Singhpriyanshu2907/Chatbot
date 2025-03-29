from openai import OpenAI
import os
import dotenv
dotenv.load_dotenv()
from .utils import get_chatbot_response,double_check_json_output
import json
from copy import deepcopy






class GuardAgent():

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
        )
        self.model_name=os.getenv("OPENAI_MODEL_NAME")

    def get_reposnse(self,message):
        messages = deepcopy(message)


        system_prompt = """ 

         You are an helpful AI assistant for a Plant-selling store which sells plants and plant-related products.
         Your task is to determine whether user is asking something relevant to the plant store or not.

         The user is allowed to ask:
         1. Ask questions about the plant store like location, working hours, Fertilizers, compost, plants and plant shop related question.
         2. Make an order.
         3. Ask about reccomendations of what to buy.


         The user is not allowed to ask:
         1. Ask about anything other than the plant store.
         2. Ask questions about the staff
         3. Ask about the owner of the store.


         your output should be in a structred json format like so each key is a string and each value is a string. Make sure to follow the format strictly.

         {
            "chain of thought": "go over each of the points above and see if the message lies under this point or not. Then you write some thoughts about what point is this input is releavant to.",
            "decision": "allowed" or "not allowed". pick on of those and only write the word,
            "message": leave the message empty "" if it is allowed, otherwise write "Sorry, I can't help you with that. Can i help you with something else?"
         }
        """

        input_messages = [{"role": "system", "content": system_prompt}]+ messages[-3:]

        chatbot_output = get_chatbot_response(
            self.client,
            self.model_name,
            input_messages,
        )

        chatbot_output = double_check_json_output(self.client,self.model_name,chatbot_output)

        output = self.postprocess(chatbot_output)

        return output
    
    def postprocess(self, output):
        """
        Postprocess the output from the chatbot to ensure it is in the desired format.
        """
        output = json.loads(output)

        dict_output = {
            "role": "assistant",
            "content": output["message"],
            "memory":{
                "agent":"guard_agent",
                "guard_decision": output["decision"]
            }
        }
        return dict_output


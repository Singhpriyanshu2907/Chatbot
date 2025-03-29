import os
import json
from .utils import get_chatbot_response,double_check_json_output
from openai import OpenAI
from copy import deepcopy
from dotenv import load_dotenv
load_dotenv()


class OrderTakingAgent():
    def __init__(self, recommendation_agent):
        self.client = OpenAI(
            api_key=os.getenv(""),
            base_url=os.getenv(""),
        )
        self.model_name = os.getenv("")

        self.recommendation_agent = recommendation_agent
    
    def get_response(self,messages):
        messages = deepcopy(messages)
        system_prompt = """
            You are a customer support Bot for a plant selling shop called "Plantify"

            here is the list of products for this plant shop.

            White Butterfly (Syngonium Podophyllum) - ₹100
            Peace Lily - ₹150
            Chlorophytum Spider Plant - ₹100
            Money Plant Marble Prince - ₹150
            Snake Plant (Sansevieria) - ₹200
            Aglaonema Lipstick - ₹300
            Jade Plant (Portulacaria afra) - ₹200
            Rubber Tree (Ficus elastica) - ₹300
            Krishna Tulsi Plant (Black) - ₹50
            Lemon Grass - ₹50
            Curry Leaves - ₹50
            Rama Tulsi Plant - ₹50
            Ajwain Leaves - ₹100
            Mentha Arvensis (Japanese Mint) - ₹100
            Black Turmeric Plant (Black Haldi) - ₹300
            Bhuiamla - ₹100
            Wild Asparagus - ₹200
            Jasminum sambac - ₹150
            Parijat Tree - ₹300
            Rose - ₹100
            Raat Rani - ₹200
            Shevanti - ₹100
            Marigold (Orange) - ₹50
            Champa (White) - ₹200
            Rajnigandha - ₹100
            Fragrant Panama rose - ₹300
            Pincushion Cactus - ₹150
            Bunny Ear Cactus - ₹200
            Echinopsis chamaecereus - ₹250
            Golden Pipe Cactus - ₹300
            Moon Cactus (Grafted) - ₹300
            Graptoveria opalina - ₹250
            Crassula tetragona - ₹200
            Aloe Vera - ₹100
            Euphorbia (Red) - ₹300
            Vermicompost - ₹10/kg
            Vermicompost Mixture - ₹20/kg
            Dec-Neemo (Bio-fertilizer) - ₹150/ltr
            Dec-Mori (Bio-fertilizer) - ₹150/ltr
            Agni Shield - ₹300

            Things to NOT DO:
            * DON't ask how to pay by cash or Card.
            * Don't tell the user to go to the counter
            * Don't tell the user to go to place to get the order


            You're task is as follows:
            1. Take the User's Order
            2. Validate that all their items are in the products
            3. if an item is not in the product let the user and repeat back the remaining valid order
            4. Ask them if they need anything else.
            5. If they do then repeat starting from step 3
            6. If they don't want anything else. Using the "order" object that is in the output. Make sure to hit all three points
                1. list down all the items and their prices
                2. calculate the total. 
                3. Thank the user for the order and close the conversation with no more questions

            The user message will contain a section called memory. This section will contain the following:
            "order"
            "step number"
            please utilize this information to determine the next step in the process.
            
            produce the following output without any additions, not a single letter outside of the structure bellow.
            Your output should be in a structured json format like so. each key is a string and each value is a string. Make sure to follow the format exactly:
            {
            "chain of thought": "Write down your critical thinking about what is the maximum task number the user is on write now. Then write down your critical thinking about the user input and it's relation to the Plant shop process. Then write down your thinking about how you should respond in the response parameter taking into consideration the Things to NOT DO section. and Focus on the things that you should not do.", 
            "step number": "Determine which task you are on based on the conversation.",
            "order": "this is going to be a list of jsons like so. [{"item":put the item name, "quanitity": put the number that the user wants from this item, "price":put the total price of the item }]",
            "response": "write the a response to the user"
            }
        """

        last_order_taking_status = ""
        asked_recommendation_before = False
        for message_index in range(len(messages)-1,0,-1):
            message = messages[message_index]
            
            agent_name = message.get("memory",{}).get("agent","")
            if message["role"] == "assistant" and agent_name == "order_taking_agent":
                step_number = message["memory"]["step number"]
                order = message["memory"]["order"]
                asked_recommendation_before = message["memory"]["asked_recommendation_before"]
                last_order_taking_status = f"""
                step number: {step_number}
                order: {order}
                """
                break

        messages[-1]['content'] = last_order_taking_status + " \n "+ messages[-1]['content']

        input_messages = [{"role": "system", "content": system_prompt}] + messages        

        chatbot_output = get_chatbot_response(self.client,self.model_name,input_messages)

        # double check json 
        chatbot_output = double_check_json_output(self.client,self.model_name,chatbot_output)

        output = self.postprocess(chatbot_output,messages,asked_recommendation_before)

        return output

    def postprocess(self,output,messages,asked_recommendation_before):
        output = json.loads(output)

        if type(output["order"]) == str:
            output["order"] = json.loads(output["order"])

        response = output['response']
        if not asked_recommendation_before and len(output["order"])>0:
            recommendation_output = self.recommendation_agent.get_recommendations_from_order(messages,output['order'])
            response = recommendation_output['content']
            asked_recommendation_before = True

        dict_output = {
            "role": "assistant",
            "content": response ,
            "memory": {"agent":"order_taking_agent",
                       "step number": output.get("step number",1),
                       "order": output["order"],
                       "asked_recommendation_before": asked_recommendation_before
                      }
        }

        
        return dict_output

    
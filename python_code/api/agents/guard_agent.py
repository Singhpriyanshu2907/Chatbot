import os
import json
from copy import deepcopy
import boto3
from .utils import get_chatbot_response

class GuardAgent():
    def __init__(self):
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.model_name = os.getenv("BEDROCK_MODEL_NAME", "mistral.mistral-7b-instruct-v0:2")

    def get_response(self, message):
        messages = deepcopy(message)

        system_prompt = """<<SYS>>
You are a helpful AI assistant for a plant-selling store that offers plants and plant-related products.

Your task is to determine if the user's question or request is allowed based on the following rules:

The user is **allowed** to:
1. Ask questions about the plant store (e.g., location, working hours, plants, fertilizers, compost, or any plant shop-related topic).
2. Place an order or inquire about ordering any plants or plant products.
3. Ask for recommendations on what to buy.
4. Ask about ordering, adding, or purchasing any plant-related items.

The user is **not allowed** to:
1. Ask about topics completely unrelated to plants or the plant store (e.g., politics, news, entertainment).
2. Ask personal questions about the store staff.
3. Ask personal questions about the store owner.

You must provide your answer strictly in the following JSON format (no extra text, no code block):

{
    "chain_of_thought": "Explain briefly which rule the user's input matches",
    "decision": "allowed" or "not allowed",
    "message": "Your response to the user. If 'not allowed', reply exactly with: 'Sorry, I can't help you with that. Can I help you with something else?'"
}

IMPORTANT RULES:
- ANY plant-related request should be allowed, even if it's about ordering
- If the message mentions plant names, ordering, or purchasing, it's allowed
- If the message is ambiguous but could be plant-related, mark it as allowed
- When in doubt, choose "allowed" rather than "not allowed"
<</SYS>>"""


        # Prepare messages in Mistral format
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        # Get response from Mistral
        chatbot_output = get_chatbot_response(
            client=self.client,
            model_name=self.model_name,
            messages=input_messages,
            temperature=0.1  # Lower temperature for more deterministic decisions
        )

        # Clean and verify the output
        chatbot_output = self.clean_json_output(chatbot_output)
        output = self.postprocess(chatbot_output)

        return output

    def clean_json_output(self, output):
        """Ensure the output is valid JSON with all required fields"""
        try:
            # Remove any code blocks and whitespace
            output = output.strip().replace("```json", "").replace("```", "")
            
            # Parse JSON
            parsed = json.loads(output)
            
            # Validate required fields
            required_fields = ["chain_of_thought", "decision", "message"]
            if not all(field in parsed for field in required_fields):
                raise ValueError("Missing required fields in JSON output")
                
            # Validate decision values
            if parsed["decision"] not in ["allowed", "not allowed"]:
                raise ValueError("Invalid decision value")
                
            return parsed
            
        except (json.JSONDecodeError, ValueError) as e:
            # Default to allowed for plant-related queries
            return {
                "chain_of_thought": f"Invalid response: {str(e)}. Defaulting to allowed as safeguard.",
                "decision": "allowed",
                "message": "I'd be happy to help with your plant-related query. What would you like to know?"
            }

    def postprocess(self, output):
        """
        Postprocess the output from the chatbot to ensure it is in the desired format.
        """
        if not isinstance(output, dict):
            output = {
                "chain_of_thought": "Invalid response format",
                "decision": "allowed",
                "message": "I'd be happy to help with your plant-related query. What would you like to know?"
            }

        # Ensure message is never empty for 'not allowed' decisions
        if output.get("decision", "not allowed") == "not allowed":
            output["message"] = output.get("message") or "Sorry, I can't help you with that. Can I help you with something else?"

        dict_output = {
            "role": "assistant",
            "content": output.get("message", ""),
            "memory": {
                "agent": "guard_agent",
                "guard_decision": output.get("decision", "not allowed"),
                "chain_of_thought": output.get("chain_of_thought", "")
            }
        }
        return dict_output
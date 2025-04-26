from dotenv import load_dotenv
import os
import json
from copy import deepcopy
import boto3
from .utils import get_chatbot_response

load_dotenv()

class ClassificationAgent():
    def __init__(self):
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.model_name = os.getenv("BEDROCK_MODEL_NAME", "mistral.mistral-7b-instruct-v0:2")
    
    def get_response(self, messages):
        messages = deepcopy(messages)

        system_prompt = """<<SYS>>
You are a helpful AI assistant working for a Plant Shop application.

Your main task is to decide which specialized agent should handle the user's message.  
There are two agents you can choose from:

1. **details_agent**:  
   This agent handles questions only about:
   - Plant shop location
   - Plant shop working hours
   - Plant shop history
   - Delivery locations
   - Product collection and inventory
   - Prices of products

2. **order_taking_agent**:  
   This agent manages conversations where the user wants to place an order or is completing a purchase.

You must output your answer in the following strict JSON format:

{
    "chain_of_thought": "Explain why you chose a specific agent based on the user's message",
    "decision": "details_agent | order_taking_agent",
    "message": ""
}

Important:  
- Think carefully about the user's input before choosing the agent.  
- Follow the JSON format exactly without adding any extra text outside of it.
<</SYS>>"""
        
        # Format messages for Mistral
        formatted_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output = get_chatbot_response(
            client=self.client,
            model_name=self.model_name,
            messages=formatted_messages,
            temperature=0.3  # Lower temperature for more consistent routing
        )

        # Clean and verify JSON output
        chatbot_output = self.clean_json_output(chatbot_output)
        output = self.postprocess(chatbot_output)
        return output

    def clean_json_output(self, output):
        """Ensure the output is valid JSON"""
        try:
            # Remove any markdown code blocks
            output = output.replace("```json", "").replace("```", "").strip()
            return json.loads(output)
        except json.JSONDecodeError:
            # Fallback to details agent if parsing fails
            return {
                "chain_of_thought": "Failed to parse response - defaulting to details agent",
                "decision": "details_agent",
                "message": ""
            }

    def postprocess(self, output):
        """Convert to standard agent output format"""
        if not isinstance(output, dict):
            output = {
                "chain_of_thought": "Invalid response format",
                "decision": "details_agent",
                "message": ""
            }

        return {
            "role": "assistant",
            "content": output.get("message", ""),
            "memory": {
                "agent": "classification_agent",
                "classification_decision": output.get("decision", "details_agent")
            }
        }
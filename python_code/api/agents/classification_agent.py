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

        # Extract conversation context
        context = self._extract_conversation_context(messages)
        
        system_prompt = f"""<<SYS>>
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
   - This includes ANY intent to buy, add to cart, checkout, or modify an order
   - ANY message with words like "order", "add", "buy", "purchase", or "get" followed by a plant name
   - Also includes follow-up messages during an ordering process
   - Any message about quantities, ordering, adding plants/products
   - Any message that continues an ongoing order conversation

Conversation Context: {context}

You must output your answer in the following strict JSON format:

{{
    "chain_of_thought": "Explain why you chose a specific agent based on the user's message",
    "decision": "details_agent | order_taking_agent",
    "message": ""
}}

IMPORTANT RULES:
- ANY message that could be interpreted as wanting to purchase a plant should go to order_taking_agent
- If the message contains "add", "order", "buy", "purchase", "get" + any plant name, ALWAYS route to order_taking_agent
- When in doubt about ordering intent, choose order_taking_agent
- If the user is in the middle of ordering, ALWAYS route to order_taking_agent
- Follow the JSON format exactly without adding any extra text outside of it.
<</SYS>>"""
        
        # Format messages for Mistral - include up to last 5 messages for context
        formatted_messages = [{"role": "system", "content": system_prompt}] + messages[-5:]

        chatbot_output = get_chatbot_response(
            client=self.client,
            model_name=self.model_name,
            messages=formatted_messages,
            temperature=0.2  # Lower temperature for more consistent routing
        )

        # Clean and verify JSON output
        chatbot_output = self.clean_json_output(chatbot_output)
        output = self.postprocess(chatbot_output)
        return output
    
    def _extract_conversation_context(self, messages):
        """Extract context from previous messages to improve routing decisions"""
        context = {
            "in_ordering_process": False,
            "last_agent": None,
            "has_cart_items": False
        }
        
        # Analyze previous messages to detect ongoing order context
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("memory"):
                memory = msg.get("memory", {})
                agent = memory.get("agent")
                
                # Track which agent handled previous messages
                if agent:
                    context["last_agent"] = agent
                
                # Check if ordering process is active
                if agent == "order_taking_agent":
                    context["in_ordering_process"] = True
                    
                    # Check if cart has items
                    if "cart" in memory and memory["cart"]:
                        context["has_cart_items"] = True
        
        # Convert to string representation for prompt
        return (
            f"Previous agent: {context['last_agent'] or 'None'}. "
            f"{'User is in an ordering process. ' if context['in_ordering_process'] else ''}"
            f"{'User has items in cart. ' if context['has_cart_items'] else ''}"
        )

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
                "classification_decision": output.get("decision", "details_agent"),
                "chain_of_thought": output.get("chain_of_thought", "")
            }
        }
from typing import Dict, Any, List
from .guard_agent import GuardAgent
from .classification_agent import ClassificationAgent
from .details_agent import DetailsAgent
from .order_taking_agent import OrderTakingAgent

class RouterAgent:
    """
    Main router that orchestrates the flow between different agents
    """
    def __init__(self):
        self.guard_agent = GuardAgent()
        self.classification_agent = ClassificationAgent()
        self.details_agent = DetailsAgent()
        self.order_taking_agent = OrderTakingAgent()
        
    def process_message(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a user message through the appropriate agent pipeline
        
        Args:
            messages: List of message dictionaries in the conversation history
            
        Returns:
            A response dictionary from the appropriate agent
        """
        print(f"=== New Request === User Input: {messages[-1]['content']}")
        
        # Step 1: Guard Agent - First line of defense
        guard_response = self.guard_agent.get_response(messages)
        
        # If not allowed, return guard response
        if guard_response["memory"]["guard_decision"] == "not allowed":
            print(f"Routing to: guard_agent (blocked)")
            return guard_response
            
        # Step 2: Order Detection Fast Path
        # Check for obvious ordering intent keywords to bypass classification
        latest_message = messages[-1]['content'].lower()
        order_keywords = ["order", "buy", "purchase", "add", "cart", "checkout"]
        if any(keyword in latest_message for keyword in order_keywords):
            print(f"Routing to: order_taking_agent (fast path)")
            return self.order_taking_agent.get_response(messages)
        
        # Step 3: Classification Agent
        classification_response = self.classification_agent.get_response(messages)
        agent_decision = classification_response["memory"]["classification_decision"]
        print(f"Routing to: {agent_decision}")
        
        # Step 4: Route to appropriate agent
        if agent_decision == "order_taking_agent":
            return self.order_taking_agent.get_response(messages)
        else:
            # Step 5: Route to details agent
            details_response = self.details_agent.get_response(messages)
            
            # Step 6: Detect if details agent flagged for rerouting to order agent
            if "needs_rerouting" in details_response.get("memory", {}) and details_response["memory"]["needs_rerouting"]:
                print(f"Rerouting order intent to: order_taking_agent")
                return self.order_taking_agent.get_response(messages)
                
            return details_response
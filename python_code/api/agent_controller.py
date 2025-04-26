from datetime import datetime
from python_code.api.agents import (
    GuardAgent,
    ClassificationAgent,
    DetailsAgent,
    OrderTakingAgent
)
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)

class AgentController:
    def __init__(self):
        try:
            
            # Initialize dependent agents
            self.order_taking_agent = OrderTakingAgent()
            self.guard_agent = GuardAgent()
            self.classification_agent = ClassificationAgent()
            self.details_agent = DetailsAgent()

            self.agent_dict = {
                "guard_agent": self.guard_agent,
                "classification_agent": self.classification_agent,
                "details_agent": self.details_agent,
                "order_taking_agent": self.order_taking_agent,
            }

        except Exception as e:
            logger.error(f"AgentController initialization failed: {str(e)}")
            raise

    def get_response(self, input_data: dict) -> dict:
        """Simplified agent workflow without recommendations"""
        try:
            print(f"\n=== New Request ===")
            messages = input_data["input"]["messages"]
            user_input = messages[-1]['content']
            print(f"User Input: {user_input}")

            # Step 1: Guard Agent Filtering
            guard_response = self.guard_agent.get_response(messages)
            if guard_response.get("memory", {}).get("guard_decision") == "not allowed":
                print(f"Routing to: guard_agent (blocked)")
                return guard_response

            # Step 2: Classification Agent Routing
            classification_response = self.classification_agent.get_response(messages)
            target_agent = classification_response.get("memory", {}).get(
                "classification_decision", 
                "details_agent"  # Default fallback
            )
            print(f"Routing to: {target_agent}")

            # Step 3: Route to Specialized Agent
            if target_agent == "details_agent":
                return self.details_agent.get_response(messages)
            return self.order_taking_agent.get_response(messages)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {
                "role": "assistant",
                "content": "Sorry, I'm experiencing technical difficulties. Please try again later.",
                "memory": {"agent": "controller"}
            }
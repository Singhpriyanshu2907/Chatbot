from typing import Protocol, Any, Dict, List, Optional, Union

class AgentProtocol(Protocol):
    def get_response(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get a response from the agent based on the conversation history.
        
        Args:
            messages: List of message dictionaries containing:
                - role (str): 'user' or 'assistant'
                - content (str): The message content
                - memory (Optional[Dict]): Agent-specific memory (optional)
                
        Returns:
            Dictionary containing:
                - role (str): Always 'assistant'
                - content (str): The response text
                - memory (Dict): Agent-specific memory including:
                    - agent (str): Agent type identifier
                    - [agent-specific fields]
        """
        ...
from typing import Protocol, Any, Dict,List


class AgentProtocol(Protocol):

    def get_response(self,message:List[Dict[str, Any]]) -> Dict[str,Any]:

        ...
        """Get a response from the agent based on the provided message.

        Args:
            message (List[Dict[str, Any]]): The message to process.

        Returns:
            str: The response from the agent.
        """
        
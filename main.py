from python_code.api.agent_controller import AgentController
import streamlit as st
from typing import Dict, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_chat_session():
    """Initialize the chat session and agent controller"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'controller' not in st.session_state:
        try:
            st.session_state.controller = AgentController()
        except Exception as e:
            st.error(f"❌ Failed to initialize chatbot: {str(e)}")
            st.stop()

def display_chat_messages():
    """Display all chat messages in the Streamlit app"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def process_user_input(user_input: str):
    """Process user input and generate assistant response"""
    try:
        input_data = {
            "input": {
                "messages": st.session_state.messages + [{"role": "user", "content": user_input}]
            }
        }
        
        # Get agent response
        response = st.session_state.controller.get_response(input_data)
        
        # Add messages to session state
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["content"]
        })
        
    except Exception as e:
        st.error(f"Error processing message: {str(e)}")
        logger.error("Chat error: %s", str(e))

def main():
    st.set_page_config(
        page_title="Plantify Chat Assistant",
        page_icon="🌿",
        layout="wide"
    )
    
    st.title("🌿 Plantify Chat Assistant")
    st.caption("Ask me about plants or place an order!")
    
    # Initialize chat session
    initialize_chat_session()
    
    # Display chat messages
    display_chat_messages()
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about plants..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process and display assistant response
        with st.spinner("Thinking..."):
            process_user_input(prompt)
        
        # Rerun to display new messages
        st.rerun()

if __name__ == "__main__":
    main()
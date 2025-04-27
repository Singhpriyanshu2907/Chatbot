# main.py
import streamlit as st
from python_code.api.agents.router import RouterAgent
import json


# Modified CSS with better contrast
# Set page configuration first
st.set_page_config(page_title="🌿 Plantify Chat Assistant", page_icon="🌿")

# Dark theme CSS
st.markdown("""
<style>
    /* Main container */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }

    /* Chat messages */
    .stChatMessage {
        background-color: #1a1a1a;
        border-radius: 15px;
        margin: 10px 0;
    }

    /* User message bubble */
    [data-testid="stChatMessage"] > div:first-child > div:first-child {
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        border-radius: 15px 15px 0 15px;
    }

    /* Bot message bubble */
    [data-testid="stChatMessage"] > div:first-child > div:last-child {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border-radius: 15px 15px 15px 0;
        border: 1px solid #404040 !important;
    }

    /* Input box */
    .stChatInput input {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
        border-radius: 10px !important;
    }

    /* Header */
    .header {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #404040;
    }

    /* Sidebar */
    .sidebar .stMarkdown {
        color: #ffffff !important;
    }

    /* JSON debug info */
    .stJson {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }

    /* Expander header */
    .streamlit-expanderHeader {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! I'm Plantify 🌿, your plant shopping assistant. 🌸 How can I help you today?"}
    ]
if "router" not in st.session_state:
    st.session_state.router = RouterAgent()

# Display chat messages
for message in st.session_state.messages:
    avatar = "🌻" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message.get("memory"):
            with st.expander("Technical Details"):
                mem = message["memory"].copy()
                if mem.get("agent") == "details_agent":
                    mem.pop("sources", None)
                    mem.pop("documents_used", None)
                st.json(mem)

# Chat input with custom placeholder
user_input = st.chat_input("Ask about plants, place orders, or get recommendations...")

if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Get bot response with loading animation
    with st.spinner("🌱 Growing a response..."):
        try:
            response = st.session_state.router.process_message(st.session_state.messages)
        except Exception as e:
            response = {
                "role": "assistant",
                "content": "🌧️ Oops! There was a little shower of problems. Please try again!",
                "memory": {"error": str(e)}
            }

    # Add assistant response to chat history
    st.session_state.messages.append(response)

    # Display assistant response
    with st.chat_message("assistant", avatar="🌻"):
        st.markdown(response["content"])
        if response.get("memory"):
            with st.expander("Technical Details"):
                mem = response["memory"].copy()
                if mem.get("agent") == "details_agent":
                    mem.pop("sources", None)
                    mem.pop("documents_used", None)
                st.json(mem)

# Sidebar with additional information
with st.sidebar:
    st.markdown("""
    <div style="text-align:center">
        <h2>🌿 Plantify Store</h2>
        <p>Your Urban Gardening Partner</p>
        <hr>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**📍 Store Locations**")
    st.write("- Lucknow\n- Hardoi\n- Barabanki\n- Sandila")
    
    st.markdown("**⏰ Opening Hours**")
    st.write("Daily 10 AM – 8 PM")
    
    st.markdown("**📞 Contact Us**")
    st.write("+91 8960121212\nhello@plantify.in")
    
    st.markdown("---")
    st.markdown("_✨ Caring for plants, nurturing lives_")
"""
config.py

Loads environment variables and initialises the shared LLM client.
Import `get_client()` from here wherever the LLM is needed —
this always picks up the latest GROQ_API_KEY from the environment
(including keys entered via the sidebar at runtime).
"""

import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# Module-level client for backwards compatibility
client = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY", ""),
    temperature=0.2,
    max_tokens=1024,
)


def get_client():
    """
    Returns a ChatGroq or ChatNVIDIA client using the correct API KEY.
    For demo users, uses ChatNVIDIA and NVIDIA_API_KEY.
    For real users, uses ChatGroq and GROQ_API_KEY.
    """
    import os
    import streamlit as st
    
    is_guest = False
    try:
        is_guest = st.session_state.get("is_guest", False)
    except Exception:
        pass

    if is_guest:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        api_key = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY", "")
        return ChatNVIDIA(
            model="meta/llama-3.3-70b-instruct",
            api_key=api_key,
            temperature=0.2,
            max_tokens=1024,
        )
    else:
        from langchain_groq import ChatGroq
        try:
            api_key = st.session_state.get("api_key") or os.getenv("GROQ_API_KEY", "")
        except Exception:
            api_key = os.getenv("GROQ_API_KEY", "")
            
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=api_key,
            temperature=0.2,
            max_tokens=1024,
        )

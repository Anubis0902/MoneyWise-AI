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
    from dotenv import load_dotenv

    load_dotenv(override=True)
    
    is_guest = False
    try:
        is_guest = st.session_state.get("is_guest", False)
    except Exception:
        pass

    # For guest, force NVIDIA demo
    if is_guest:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        api_key = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY", "")
        return ChatNVIDIA(
            model="meta/llama-3.3-70b-instruct",
            api_key=api_key,
            temperature=0.2,
            max_tokens=1024,
        )

    # For logged-in users, try Groq first, then fallback to NVIDIA
    from langchain_groq import ChatGroq
    try:
        groq_key = st.session_state.get("api_key") or os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        groq_key = os.getenv("GROQ_API_KEY", "")
        
    if groq_key:
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.2,
            max_tokens=1024,
        )
        
    # Fallback to NVIDIA if no Groq key is found but NVIDIA is available
    nvidia_key = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY", "")
    if nvidia_key:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        return ChatNVIDIA(
            model="meta/llama-3.3-70b-instruct",
            api_key=nvidia_key,
            temperature=0.2,
            max_tokens=1024,
        )
        
    # Return Groq by default (will fail gracefully later if empty)
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key="",
        temperature=0.2,
        max_tokens=1024,
    )
